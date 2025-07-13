#!/usr/bin/env python3
"""
S3 Public File Manager
A universal tool to make files public on S3-compatible storage services.

Supports:
- Amazon S3
- DigitalOcean Spaces
- Wasabi
- Backblaze B2
- MinIO
- And other S3-compatible services

Author: Daniele Caluri
Version: 1.0.0
Date: 2025-07-13
https://caluri.it
License: MIT
"""

import boto3
import argparse
import json
import os
import sys
from typing import Dict, List, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class S3PublicManager:
    """Universal S3-compatible storage manager for making files public."""
    
    # Predefined service configurations
    SERVICES = {
        'aws': {
            'name': 'Amazon S3',
            'endpoint_url': None,
            'regions': ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        },
        'digitalocean': {
            'name': 'DigitalOcean Spaces',
            'endpoint_url': 'https://{region}.digitaloceanspaces.com',
            'regions': ['nyc3', 'ams3', 'sgp1', 'fra1', 'sfo3', 'tor1', 'blr1']
        },
        'wasabi': {
            'name': 'Wasabi',
            'endpoint_url': 'https://s3.{region}.wasabisys.com',
            'regions': ['us-east-1', 'us-east-2', 'us-west-1', 'eu-central-1', 'ap-northeast-1']
        },
        'backblaze': {
            'name': 'Backblaze B2',
            'endpoint_url': 'https://s3.{region}.backblazeb2.com',
            'regions': ['us-west-002', 'eu-central-003']
        },
        'minio': {
            'name': 'MinIO',
            'endpoint_url': 'http://localhost:9000',
            'regions': ['us-east-1']
        }
    }
    
    def __init__(self, service: str, region: str, access_key: str, secret_key: str, 
                 endpoint_url: Optional[str] = None):
        """
        Initialize the S3 manager.
        
        Args:
            service: Service name (aws, digitalocean, wasabi, backblaze, minio, custom)
            region: Region name
            access_key: Access key ID
            secret_key: Secret access key
            endpoint_url: Custom endpoint URL (overrides service default)
        """
        self.service = service
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        
        # Determine endpoint URL
        if endpoint_url:
            self.endpoint_url = endpoint_url
        elif service in self.SERVICES:
            endpoint_template = self.SERVICES[service]['endpoint_url']
            self.endpoint_url = endpoint_template.format(region=region) if endpoint_template else None
        else:
            self.endpoint_url = None
        
        # Initialize boto3 client
        self.client = self._create_client()
    
    def _create_client(self):
        """Create and return a boto3 S3 client."""
        try:
            client_config = {
                'region_name': self.region,
                'aws_access_key_id': self.access_key,
                'aws_secret_access_key': self.secret_key,
            }
            
            if self.endpoint_url:
                client_config['endpoint_url'] = self.endpoint_url
            
            return boto3.client('s3', **client_config)
        except Exception as e:
            logger.error(f"Failed to create S3 client: {e}")
            raise
    
    def list_buckets(self) -> List[str]:
        """List all available buckets."""
        try:
            response = self.client.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]
        except ClientError as e:
            logger.error(f"Failed to list buckets: {e}")
            return []
    
    def list_objects(self, bucket_name: str, prefix: str = '', recursive: bool = True) -> List[Dict]:
        """
        List objects in a bucket with optional prefix.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Object prefix to filter by
            recursive: If True, include all subdirectories (default: True)
            
        Returns:
            List of object information dictionaries
        """
        try:
            objects = []
            paginator = self.client.get_paginator('list_objects_v2')
            
            # Configure pagination parameters
            page_params = {
                'Bucket': bucket_name,
                'Prefix': prefix
            }
            
            # If not recursive, add delimiter to only get direct children
            if not recursive:
                page_params['Delimiter'] = '/'
            
            logger.debug(f"Listing objects with params: {page_params}")
            
            page_count = 0
            for page in paginator.paginate(**page_params):
                page_count += 1
                logger.debug(f"Processing page {page_count}")
                
                if 'Contents' in page:
                    page_objects = page['Contents']
                    logger.debug(f"Found {len(page_objects)} objects in page {page_count}")
                    objects.extend(page_objects)
                
                # Also check for common prefixes (subdirectories) if not recursive
                if 'CommonPrefixes' in page and not recursive:
                    logger.debug(f"Found {len(page['CommonPrefixes'])} subdirectories")
                    for prefix_info in page['CommonPrefixes']:
                        logger.debug(f"Subdirectory: {prefix_info['Prefix']}")
            
            logger.info(f"Total objects found: {len(objects)}")
            
            # Log some examples of what we found
            if objects:
                logger.debug("Sample objects found:")
                for i, obj in enumerate(objects[:5]):  # Show first 5
                    logger.debug(f"  {i+1}. {obj['Key']} ({obj.get('Size', 0)} bytes)")
                if len(objects) > 5:
                    logger.debug(f"  ... and {len(objects) - 5} more objects")
            
            return objects
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    def make_object_public(self, bucket_name: str, object_key: str) -> bool:
        """
        Make a single object public.
        
        Args:
            bucket_name: Name of the bucket
            object_key: Key of the object to make public
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.put_object_acl(
                Bucket=bucket_name,
                Key=object_key,
                ACL='public-read'
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to make object public {object_key}: {e}")
            return False
    
    def make_objects_public(self, bucket_name: str, prefix: str = '', 
                          dry_run: bool = False, recursive: bool = True) -> Dict[str, int]:
        """
        Make multiple objects public based on prefix.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Object prefix to filter by
            dry_run: If True, only show what would be done
            recursive: If True, include all subdirectories (default: True)
            
        Returns:
            Dictionary with success and failure counts
        """
        logger.info(f"Searching for objects with prefix '{prefix}' (recursive: {recursive})")
        objects = self.list_objects(bucket_name, prefix, recursive)
        
        if not objects:
            logger.warning(f"No objects found with prefix '{prefix}' in bucket '{bucket_name}'")
            
            # Try to help debug the issue
            logger.info("Attempting to list all objects in bucket to help debug...")
            all_objects = self.list_objects(bucket_name, '', recursive=True)
            
            if all_objects:
                logger.info(f"Found {len(all_objects)} total objects in bucket. Sample paths:")
                unique_prefixes = set()
                for obj in all_objects[:20]:  # Show first 20
                    path = obj['Key']
                    logger.info(f"  - {path}")
                    # Extract directory structure
                    if '/' in path:
                        dir_path = '/'.join(path.split('/')[:-1]) + '/'
                        unique_prefixes.add(dir_path)
                
                if unique_prefixes:
                    logger.info(f"Detected directory structures:")
                    for prefix_found in sorted(unique_prefixes)[:10]:
                        logger.info(f"  - {prefix_found}")
                    logger.info(f"Try using one of these prefixes: {sorted(unique_prefixes)[:5]}")
            else:
                logger.warning("No objects found in the entire bucket")
            
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"Found {len(objects)} objects to process")
        
        # Filter out directory markers (objects ending with /)
        file_objects = [obj for obj in objects if not obj['Key'].endswith('/')]
        dir_markers = len(objects) - len(file_objects)
        
        if dir_markers > 0:
            logger.info(f"Skipping {dir_markers} directory markers")
        
        if not file_objects:
            logger.warning("No actual files found (only directory markers)")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"Processing {len(file_objects)} actual files")
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info("Files that would be made public:")
            for obj in file_objects:
                logger.info(f"  - {obj['Key']} ({obj.get('Size', 0)} bytes)")
            return {'success': 0, 'failed': 0, 'total': len(file_objects)}
        
        success_count = 0
        failed_count = 0
        
        for i, obj in enumerate(file_objects, 1):
            object_key = obj['Key']
            logger.info(f"[{i}/{len(file_objects)}] Processing: {object_key}")
            
            if self.make_object_public(bucket_name, object_key):
                logger.info(f"✓ Made public: {object_key}")
                success_count += 1
            else:
                logger.error(f"✗ Failed: {object_key}")
                failed_count += 1
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(file_objects)
        }
    
    def get_public_url(self, bucket_name: str, object_key: str) -> str:
        """
        Get the public URL for an object.
        
        Args:
            bucket_name: Name of the bucket
            object_key: Key of the object
            
        Returns:
            Public URL string
        """
        if self.service == 'aws':
            return f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        elif self.service == 'digitalocean':
            return f"https://{bucket_name}.{self.region}.digitaloceanspaces.com/{object_key}"
        elif self.endpoint_url:
            # Generic S3-compatible URL
            base_url = self.endpoint_url.replace('https://', '').replace('http://', '')
            return f"https://{bucket_name}.{base_url}/{object_key}"
        else:
            return f"https://{bucket_name}.s3.{self.region}.amazonaws.com/{object_key}"


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        return {}


def create_sample_config():
    """Create a sample configuration file."""
    sample_config = {
        "service": "digitalocean",
        "region": "fra1",
        "access_key": "YOUR_ACCESS_KEY",
        "secret_key": "YOUR_SECRET_KEY",
        "bucket_name": "your-bucket-name",
        "prefix": "path/to/files/",
        "recursive": true,
        "endpoint_url": null
    }
    
    with open('config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    logger.info("Sample configuration file created: config.json")
    logger.info("Please edit the configuration file with your credentials.")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Make files public on S3-compatible storage services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use configuration file
  python s3_public_manager.py --config config.json

  # Command line arguments
  python s3_public_manager.py --service digitalocean --region fra1 \\
    --access-key YOUR_KEY --secret-key YOUR_SECRET \\
    --bucket my-bucket --prefix images/

  # Dry run to see what would be changed
  python s3_public_manager.py --config config.json --dry-run

  # List available buckets
  python s3_public_manager.py --config config.json --list-buckets

  # Create sample configuration file
  python s3_public_manager.py --create-config

Supported services:
  - aws (Amazon S3)
  - digitalocean (DigitalOcean Spaces)
  - wasabi (Wasabi)
  - backblaze (Backblaze B2)
  - minio (MinIO)
  - custom (Custom S3-compatible service)
        """
    )
    
    # Configuration options
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--create-config', action='store_true', 
                       help='Create a sample configuration file')
    
    # Service configuration
    parser.add_argument('--service', choices=['aws', 'digitalocean', 'wasabi', 'backblaze', 'minio', 'custom'],
                       help='Storage service to use')
    parser.add_argument('--region', help='Region name')
    parser.add_argument('--access-key', help='Access key ID')
    parser.add_argument('--secret-key', help='Secret access key')
    parser.add_argument('--endpoint-url', help='Custom endpoint URL')
    
    # Operation options
    parser.add_argument('--bucket', help='Bucket name')
    parser.add_argument('--prefix', default='', help='Object prefix to filter by')
    parser.add_argument('--recursive', action='store_true', default=True,
                       help='Include subdirectories (default: True)')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false',
                       help='Only process files in the specified directory, not subdirectories')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--list-buckets', action='store_true', 
                       help='List available buckets')
    
    # Logging
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create sample config
    if args.create_config:
        create_sample_config()
        return
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Override config with command line arguments
    service = args.service or config.get('service')
    region = args.region or config.get('region')
    access_key = args.access_key or config.get('access_key') or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = args.secret_key or config.get('secret_key') or os.environ.get('AWS_SECRET_ACCESS_KEY')
    endpoint_url = args.endpoint_url or config.get('endpoint_url')
    bucket_name = args.bucket or config.get('bucket_name')
    prefix = args.prefix or config.get('prefix', '')
    recursive = args.recursive if hasattr(args, 'recursive') else config.get('recursive', True)
    
    # Validate required parameters
    if not all([service, region, access_key, secret_key]):
        logger.error("Missing required parameters. Use --help for usage information.")
        logger.error("Required: service, region, access_key, secret_key")
        sys.exit(1)
    
    try:
        # Initialize manager
        manager = S3PublicManager(service, region, access_key, secret_key, endpoint_url)
        
        # List buckets if requested
        if args.list_buckets:
            buckets = manager.list_buckets()
            if buckets:
                logger.info("Available buckets:")
                for bucket in buckets:
                    print(f"  - {bucket}")
            else:
                logger.warning("No buckets found or failed to list buckets")
            return
        
        # Validate bucket name
        if not bucket_name:
            logger.error("Bucket name is required")
            sys.exit(1)
        
        # Make objects public
        logger.info(f"Making objects public in bucket '{bucket_name}' with prefix '{prefix}'")
        results = manager.make_objects_public(bucket_name, prefix, args.dry_run, args.recursive)
        
        # Print results
        logger.info(f"Results: {results['success']} successful, {results['failed']} failed, {results['total']} total")
        
        if results['success'] > 0 and not args.dry_run:
            logger.info("Files are now publicly accessible!")
            logger.info(f"Service: {manager.SERVICES.get(service, {}).get('name', service)}")
            logger.info(f"Region: {region}")
            logger.info(f"Bucket: {bucket_name}")
            logger.info(f"Prefix: {prefix}")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()