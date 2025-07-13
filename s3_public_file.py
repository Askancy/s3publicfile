#!/usr/bin/env python3
"""
S3 Public File Manager with Animated Progress
A universal tool to make files public on S3-compatible storage services with animated progress display.

Supports:
- Amazon S3
- DigitalOcean Spaces
- Wasabi
- Backblaze B2
- MinIO
- And other S3-compatible services

Author: Daniele Caluri
Version: 1.1.0
Date: 2025-07-13
https://caluri.it
License: MIT
"""

import boto3
import argparse
import json
import os
import sys
import time
import threading
from typing import Dict, List, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import logging

# Try to import rich for better progress display
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProgressDisplay:
    """Manages animated progress display."""
    
    def __init__(self, use_rich: bool = RICH_AVAILABLE):
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = Console() if self.use_rich else None
        self.current_file = ""
        self.current_directory = ""
        self.processed_files = 0
        self.total_files = 0
        self.success_count = 0
        self.failed_count = 0
        self.start_time = None
        self.is_running = False
        self._stop_animation = False
        self._animation_thread = None
        
        # Characters for spinner animation
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_index = 0
    
    def start(self, total_files: int):
        """Start progress display."""
        self.total_files = total_files
        self.start_time = time.time()
        self.is_running = True
        self.processed_files = 0
        self.success_count = 0
        self.failed_count = 0
        
        if self.use_rich:
            self._start_rich_display()
        else:
            self._start_simple_display()
    
    def update(self, current_file: str, success: bool = True):
        """Update progress with current file."""
        self.current_file = os.path.basename(current_file)
        self.current_directory = os.path.dirname(current_file)
        self.processed_files += 1
        
        if success:
            self.success_count += 1
        else:
            self.failed_count += 1
    
    def stop(self):
        """Stop progress display."""
        self.is_running = False
        self._stop_animation = True
        
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join()
        
        self._show_final_summary()
    
    def _start_rich_display(self):
        """Start Rich display."""
        if not self.use_rich:
            return
        
        self._animation_thread = threading.Thread(target=self._rich_animation_loop)
        self._animation_thread.daemon = True
        self._animation_thread.start()
    
    def _rich_animation_loop(self):
        """Animation loop for Rich."""
        # Use Live for fixed layout at bottom
        layout = Layout()
        layout.split_column(
            Layout(self._create_info_panel(), name="info", size=6),
            Layout(self._create_stats_panel(), name="stats", size=5),
            Layout(self._create_progress_panel(), name="progress", size=3)
        )
        
        with Live(layout, console=self.console, screen=False, refresh_per_second=10) as live:
            while self.is_running and not self._stop_animation:
                # Update panels
                layout["info"].update(self._create_info_panel())
                layout["stats"].update(self._create_stats_panel())
                layout["progress"].update(self._create_progress_panel())
                
                # Refresh every 0.1 seconds
                time.sleep(0.1)
    
    def _create_progress_panel(self) -> Panel:
        """Create progress bar panel."""
        if self.total_files == 0:
            progress_bar = "░" * 30
            percentage = 0.0
        else:
            percentage = (self.processed_files / self.total_files) * 100
            filled_length = int(30 * self.processed_files / self.total_files)
            progress_bar = "█" * filled_length + "░" * (30 - filled_length)
        
        content = f"""[cyan]{progress_bar}[/cyan] {percentage:.1f}%
[white]{self.processed_files}/{self.total_files} files processed[/white]"""
        
        return Panel(content, title="[bold]Progress[/bold]", border_style="cyan")
    
    def _create_info_panel(self) -> Panel:
        """Create current information panel."""
        if not self.current_file:
            content = "[yellow]Waiting to start...[/yellow]"
        else:
            # Truncate filename if too long
            display_file = self.current_file
            if len(display_file) > 40:
                display_file = "..." + display_file[-37:]
            
            # Truncate directory if too long
            display_dir = self.current_directory or "/"
            if len(display_dir) > 50:
                display_dir = "..." + display_dir[-47:]
            
            content = f"""[green]File:[/green] {display_file}
[blue]Directory:[/blue] {display_dir}"""
        
        return Panel(content, title="[bold]Current File[/bold]", border_style="blue")
    
    def _create_stats_panel(self) -> Panel:
        """Create statistics panel."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        if self.processed_files > 0:
            avg_time = elapsed / self.processed_files
            remaining = (self.total_files - self.processed_files) * avg_time
            eta = f"{remaining:.0f}s"
            rate = f"{self.processed_files/elapsed:.1f}" if elapsed > 0 else "0"
        else:
            eta = "Calculating..."
            rate = "0"
        
        content = f"""[green]✓ Success:[/green] {self.success_count}  [red]✗ Failed:[/red] {self.failed_count}
[yellow]Time:[/yellow] {elapsed:.0f}s  [cyan]ETA:[/cyan] {eta}  [magenta]Rate:[/magenta] {rate}/s"""
        
        return Panel(content, title="[bold]Statistics[/bold]", border_style="green")
    
    def _start_simple_display(self):
        """Start simple display without Rich."""
        self._animation_thread = threading.Thread(target=self._simple_animation_loop)
        self._animation_thread.daemon = True
        self._animation_thread.start()
    
    def _simple_animation_loop(self):
        """Simple animation loop."""
        # Reserve space for display
        print("\n" * 3)  # Reserve space for display
        
        while self.is_running and not self._stop_animation:
            # Move cursor to last 3 lines
            sys.stdout.write('\033[3A')  # Move up 3 lines
            sys.stdout.write('\033[2K')  # Clear line
            
            # Spinner
            spinner = self.spinner_chars[self.spinner_index % len(self.spinner_chars)]
            self.spinner_index += 1
            
            # Simple progress bar
            if self.total_files > 0:
                progress_pct = (self.processed_files / self.total_files) * 100
                bar_length = 25
                filled_length = int(bar_length * self.processed_files / self.total_files)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # First line: current file
                current_file = self.current_file[:50] if self.current_file else "Waiting..."
                sys.stdout.write(f'\rFile: {current_file}\n')
                
                # Second line: progress bar
                sys.stdout.write(f'\r{spinner} [{bar}] {self.processed_files}/{self.total_files} ({progress_pct:.1f}%)\n')
                
                # Third line: statistics
                elapsed = time.time() - self.start_time if self.start_time else 0
                rate = f"{self.processed_files/elapsed:.1f}/s" if elapsed > 0 and self.processed_files > 0 else "0/s"
                sys.stdout.write(f'\r✓{self.success_count} ✗{self.failed_count} | Time: {elapsed:.0f}s | Rate: {rate}')
                
                sys.stdout.flush()
            
            time.sleep(0.1)
    
    def _show_final_summary(self):
        """Show final summary."""
        if self.use_rich:
            self._show_rich_summary()
        else:
            self._show_simple_summary()
    
    def _show_rich_summary(self):
        """Show final summary with Rich."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        table = Table(title="[bold green]Processing Summary[/bold green]")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total files", str(self.total_files))
        table.add_row("Files processed", str(self.processed_files))
        table.add_row("Successful", f"[green]{self.success_count}[/green]")
        table.add_row("Failed", f"[red]{self.failed_count}[/red]")
        table.add_row("Total time", f"{elapsed:.2f}s")
        
        if self.processed_files > 0:
            table.add_row("Average time per file", f"{elapsed/self.processed_files:.2f}s")
        
        self.console.print(table)
    
    def _show_simple_summary(self):
        """Show simple final summary."""
        # Move cursor below progress bar
        sys.stdout.write('\n\n\n')
        sys.stdout.write('='*60 + '\n')
        print("PROCESSING SUMMARY")
        print('='*60)
        print(f"Total files:      {self.total_files}")
        print(f"Files processed:  {self.processed_files}")
        print(f"Successful:       {self.success_count}")
        print(f"Failed:           {self.failed_count}")
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"Total time:       {elapsed:.2f}s")
            if self.processed_files > 0:
                print(f"Average time:     {elapsed/self.processed_files:.2f}s per file")
        
        print('='*60)


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
                 endpoint_url: Optional[str] = None, progress_display: Optional[ProgressDisplay] = None):
        """
        Initialize the S3 manager.
        
        Args:
            service: Service name (aws, digitalocean, wasabi, backblaze, minio, custom)
            region: Region name
            access_key: Access key ID
            secret_key: Secret access key
            endpoint_url: Custom endpoint URL (overrides service default)
            progress_display: Progress display instance
        """
        self.service = service
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.progress_display = progress_display
        
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
        
        # Initialize progress display
        if self.progress_display:
            self.progress_display.start(len(file_objects))
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info("Files that would be made public:")
            for obj in file_objects:
                logger.info(f"  - {obj['Key']} ({obj.get('Size', 0)} bytes)")
                if self.progress_display:
                    self.progress_display.update(obj['Key'], True)
                    time.sleep(0.01)  # Small pause to see animation
            
            if self.progress_display:
                self.progress_display.stop()
            
            return {'success': 0, 'failed': 0, 'total': len(file_objects)}
        
        success_count = 0
        failed_count = 0
        
        for i, obj in enumerate(file_objects, 1):
            object_key = obj['Key']
            
            # Update progress display
            if self.progress_display:
                self.progress_display.update(object_key, True)  # Update before processing
            
            logger.info(f"[{i}/{len(file_objects)}] Processing: {object_key}")
            
            success = self.make_object_public(bucket_name, object_key)
            
            if success:
                logger.info(f"✓ Made public: {object_key}")
                success_count += 1
            else:
                logger.error(f"✗ Failed: {object_key}")
                failed_count += 1
                # Update display with failure
                if self.progress_display:
                    self.progress_display.success_count -= 1
                    self.progress_display.failed_count += 1
            
            # Small pause to not overload the service
            time.sleep(0.1)
        
        # Stop progress display
        if self.progress_display:
            self.progress_display.stop()
        
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
        "recursive": True,
        "endpoint_url": None,
        "animated_progress": True
    }
    
    with open('config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    logger.info("Sample configuration file created: config.json")
    logger.info("Please edit the configuration file with your credentials.")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Make files public on S3-compatible storage services with animated progress',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use configuration file with animated progress
  python s3_public_manager.py --config config.json

  # Command line arguments with progress animation
  python s3_public_manager.py --service digitalocean --region fra1 \\
    --access-key YOUR_KEY --secret-key YOUR_SECRET \\
    --bucket my-bucket --prefix images/ --animated-progress

  # Dry run to see what would be changed (with animation)
  python s3_public_manager.py --config config.json --dry-run

  # Disable animated progress
  python s3_public_manager.py --config config.json --no-animated-progress

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

Progress Animation:
  The tool now includes an animated progress display that shows:
  - Current file being processed
  - Current directory
  - Number of files processed
  - Success/failure statistics
  - Estimated time remaining
  - Progress bar with percentage
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
    
    # Progress display options
    parser.add_argument('--animated-progress', action='store_true', default=True,
                       help='Enable animated progress display (default: True)')
    parser.add_argument('--no-animated-progress', dest='animated_progress', action='store_false',
                       help='Disable animated progress display')
    
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
    animated_progress = args.animated_progress if hasattr(args, 'animated_progress') else config.get('animated_progress', True)
    
    # Validate required parameters
    if not all([service, region, access_key, secret_key]):
        logger.error("Missing required parameters. Use --help for usage information.")
        logger.error("Required: service, region, access_key, secret_key")
        sys.exit(1)
    
    try:
        # Configure logging to not interfere with progress display
        if animated_progress:
            # Reduce logging level to WARNING to minimize interference with progress display
            logging.getLogger().setLevel(logging.WARNING)
            # Create progress display
            progress_display = ProgressDisplay()
            if not RICH_AVAILABLE:
                logger.warning("Rich library not available. Using simple progress display.")
                logger.warning("Install rich for better progress visualization: pip install rich")
        else:
            progress_display = None
        
        # Initialize manager
        manager = S3PublicManager(service, region, access_key, secret_key, endpoint_url, progress_display)
        
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
        results = manager.make_objects_public(bucket_name, prefix, args.dry_run, recursive)
        
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
