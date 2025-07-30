#!/usr/bin/env python
"""Script to set up Azure resources for Medtech RAG solution."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.logging_config import get_logger, init_logging
from src.common.config import get_config
from src.common.azure_clients import get_azure_clients

# Initialize logging
init_logging()
logger = get_logger(__name__)


class AzureResourceSetup:
    """Set up Azure resources for the Medtech RAG solution."""
    
    def __init__(self, resource_group: str, location: str = "eastus"):
        """Initialize with resource group and location."""
        self.resource_group = resource_group
        self.location = location
        self.resources = {}
    
    def check_azure_cli(self) -> bool:
        """Check if Azure CLI is installed and user is logged in."""
        try:
            # Check if az is installed
            result = subprocess.run(["az", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Azure CLI is not installed. Please install it first.")
                return False
            
            # Check if logged in
            result = subprocess.run(["az", "account", "show"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Not logged in to Azure. Please run 'az login' first.")
                return False
            
            account_info = json.loads(result.stdout)
            logger.info(f"Logged in to Azure as: {account_info.get('user', {}).get('name', 'Unknown')}")
            logger.info(f"Subscription: {account_info.get('name', 'Unknown')} ({account_info.get('id', 'Unknown')})")
            
            return True
        except Exception as e:
            logger.error(f"Error checking Azure CLI: {e}")
            return False
    
    def create_resource_group(self) -> bool:
        """Create the resource group."""
        logger.info(f"Creating resource group: {self.resource_group}")
        
        cmd = [
            "az", "group", "create",
            "--name", self.resource_group,
            "--location", self.location
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to create resource group: {result.stderr}")
            return False
        
        logger.info(f"Resource group '{self.resource_group}' created successfully")
        return True
    
    def create_storage_account(self) -> Dict[str, str]:
        """Create storage account."""
        # Generate unique storage account name (must be lowercase, 3-24 chars)
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        storage_name = f"stmedtechragdev{suffix}"
        
        logger.info(f"Creating storage account: {storage_name}")
        
        cmd = [
            "az", "storage", "account", "create",
            "--name", storage_name,
            "--resource-group", self.resource_group,
            "--location", self.location,
            "--sku", "Standard_LRS",
            "--kind", "StorageV2",
            "--access-tier", "Hot"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to create storage account: {result.stderr}")
            return {}
        
        # Get connection string
        cmd = [
            "az", "storage", "account", "show-connection-string",
            "--name", storage_name,
            "--resource-group", self.resource_group,
            "--query", "connectionString",
            "--output", "tsv"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        connection_string = result.stdout.strip()
        
        # Get account key
        cmd = [
            "az", "storage", "account", "keys", "list",
            "--account-name", storage_name,
            "--resource-group", self.resource_group,
            "--query", "[0].value",
            "--output", "tsv"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        account_key = result.stdout.strip()
        
        logger.info(f"Storage account '{storage_name}' created successfully")
        
        return {
            "name": storage_name,
            "connection_string": connection_string,
            "account_key": account_key
        }
    
    def create_cognitive_search(self) -> Dict[str, str]:
        """Create Azure Cognitive Search service."""
        search_name = "acs-medtech-rag-dev"
        
        logger.info(f"Creating Cognitive Search service: {search_name}")
        
        cmd = [
            "az", "search", "service", "create",
            "--name", search_name,
            "--resource-group", self.resource_group,
            "--location", self.location,
            "--sku", "free"  # Free tier for development
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "already exists" in result.stderr:
                logger.warning(f"Search service '{search_name}' already exists, skipping creation")
            else:
                logger.error(f"Failed to create search service: {result.stderr}")
                return {}
        
        # Get admin key
        cmd = [
            "az", "search", "admin-key", "show",
            "--service-name", search_name,
            "--resource-group", self.resource_group,
            "--query", "primaryKey",
            "--output", "tsv"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        admin_key = result.stdout.strip()
        
        endpoint = f"https://{search_name}.search.windows.net"
        
        logger.info(f"Cognitive Search service '{search_name}' ready")
        
        return {
            "name": search_name,
            "endpoint": endpoint,
            "admin_key": admin_key
        }
    
    def create_document_intelligence(self) -> Dict[str, str]:
        """Create Azure Document Intelligence service."""
        di_name = "di-medtech-rag-dev"
        
        logger.info(f"Creating Document Intelligence service: {di_name}")
        
        cmd = [
            "az", "cognitiveservices", "account", "create",
            "--name", di_name,
            "--resource-group", self.resource_group,
            "--location", self.location,
            "--kind", "FormRecognizer",
            "--sku", "F0",  # Free tier
            "--yes"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "already exists" in result.stderr:
                logger.warning(f"Document Intelligence '{di_name}' already exists, skipping creation")
            else:
                logger.error(f"Failed to create Document Intelligence: {result.stderr}")
                return {}
        
        # Get key
        cmd = [
            "az", "cognitiveservices", "account", "keys", "list",
            "--name", di_name,
            "--resource-group", self.resource_group,
            "--query", "key1",
            "--output", "tsv"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        key = result.stdout.strip()
        
        endpoint = f"https://{di_name}.cognitiveservices.azure.com/"
        
        logger.info(f"Document Intelligence service '{di_name}' ready")
        
        return {
            "name": di_name,
            "endpoint": endpoint,
            "key": key
        }
    
    def create_key_vault(self) -> Dict[str, str]:
        """Create Azure Key Vault (optional)."""
        kv_name = "kv-medtech-rag-dev"
        
        logger.info(f"Creating Key Vault: {kv_name}")
        
        cmd = [
            "az", "keyvault", "create",
            "--name", kv_name,
            "--resource-group", self.resource_group,
            "--location", self.location
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "already exists" in result.stderr:
                logger.warning(f"Key Vault '{kv_name}' already exists, skipping creation")
            else:
                logger.warning(f"Failed to create Key Vault (optional): {result.stderr}")
                return {}
        
        vault_url = f"https://{kv_name}.vault.azure.net/"
        
        logger.info(f"Key Vault '{kv_name}' ready")
        
        return {
            "name": kv_name,
            "vault_url": vault_url
        }
    
    def write_env_file(self, resources: Dict[str, Any]) -> None:
        """Write .env file with resource information."""
        env_path = Path(__file__).parent.parent / ".env"
        
        logger.info(f"Writing configuration to {env_path}")
        
        env_content = f"""# Azure Storage Account
AZURE_STORAGE_CONNECTION_STRING={resources['storage']['connection_string']}
AZURE_STORAGE_ACCOUNT_NAME={resources['storage']['name']}
AZURE_STORAGE_ACCOUNT_KEY={resources['storage']['account_key']}

# Azure Cognitive Search
AZURE_SEARCH_ENDPOINT={resources['search']['endpoint']}
AZURE_SEARCH_API_KEY={resources['search']['admin_key']}
AZURE_SEARCH_INDEX_NAME=medtech-documents

# Azure Document Intelligence (Form Recognizer)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT={resources['document_intelligence']['endpoint']}
AZURE_DOCUMENT_INTELLIGENCE_KEY={resources['document_intelligence']['key']}

# Azure Key Vault (Optional)
AZURE_KEY_VAULT_URL={resources.get('key_vault', {}).get('vault_url', '')}

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
API_PORT=8000
API_HOST=0.0.0.0
"""
        
        with open(env_path, "w") as f:
            f.write(env_content)
        
        logger.info("Configuration written to .env file")
    
    def setup_all_resources(self) -> bool:
        """Set up all Azure resources."""
        # Check Azure CLI
        if not self.check_azure_cli():
            return False
        
        # Create resource group
        if not self.create_resource_group():
            return False
        
        # Create services
        resources = {
            "storage": self.create_storage_account(),
            "search": self.create_cognitive_search(),
            "document_intelligence": self.create_document_intelligence(),
            "key_vault": self.create_key_vault()  # Optional
        }
        
        # Check if all required resources were created
        required = ["storage", "search", "document_intelligence"]
        for resource in required:
            if not resources.get(resource):
                logger.error(f"Failed to create required resource: {resource}")
                return False
        
        # Write .env file
        self.write_env_file(resources)
        
        # Create storage containers
        logger.info("Creating storage containers...")
        try:
            config = get_config()
            clients = get_azure_clients()
            clients.create_containers_if_not_exists()
            logger.info("Storage containers created successfully")
        except Exception as e:
            logger.error(f"Failed to create storage containers: {e}")
            logger.info("You may need to create them manually or run this script again")
        
        logger.info("\n" + "="*50)
        logger.info("Azure resources setup completed successfully!")
        logger.info("="*50)
        logger.info("\nNext steps:")
        logger.info("1. Review the .env file and update any settings if needed")
        logger.info("2. Run tests to verify connections: pytest -m integration")
        logger.info("3. Start building your application!")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up Azure resources for Medtech RAG solution"
    )
    parser.add_argument(
        "--resource-group",
        default="rg-medtech-rag-dev",
        help="Name of the resource group to create (default: rg-medtech-rag-dev)"
    )
    parser.add_argument(
        "--location",
        default="eastus",
        help="Azure region for resources (default: eastus)"
    )
    
    args = parser.parse_args()
    
    setup = AzureResourceSetup(
        resource_group=args.resource_group,
        location=args.location
    )
    
    success = setup.setup_all_resources()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()