# S3 Public File Manager

<p align="center">
<img width="600" alt="S3 Public File Manager" src="https://github.com/user-attachments/assets/030b6476-a60b-4453-9c55-cff3fdb71b37" />
</p>

A universal tool to make files public on S3-compatible storage services with **animated progress display**.

Supports AWS S3, DigitalOcean Spaces, Wasabi, Backblaze B2, MinIO, and other S3-compatible services.

## ✨ **Features**

- 🎯 **Universal S3 compatibility** - Works with all major S3-compatible services
- 🎨 **Animated progress display** - Real-time progress bars and statistics
- 🔍 **Dry-run mode** - Preview changes safely before applying
- 📁 **Recursive processing** - Handle entire directory structures
- ⚙️ **Flexible configuration** - JSON config files or command-line arguments
- 🛡️ **Safe operation** - Built-in safeguards and validation

## ⚠️ **DISCLAIMER**

**USE AT YOUR OWN RISK.** This tool modifies file permissions on your cloud storage. The authors are not responsible for any damages, data loss, security issues, or problems caused by the use of this software. Always test with `--dry-run` first and ensure you understand the implications of making files publicly accessible.

## 📦 **Installation**

### Basic Installation
```bash
pip install boto3
```

### Enhanced Progress Display (Recommended)
```bash
pip install boto3 rich
```

> **Note:** Installing `rich` provides a beautiful animated progress display with panels and enhanced visuals. Without it, the tool falls back to a simple progress bar.

## 🚀 **Quick Start**

### 1. Create Configuration File
```bash
python s3_public_manager.py --create-config
```

### 2. Edit Configuration
Edit the generated `config.json` with your credentials:

```json
{
  "service": "digitalocean",
  "region": "fra1",
  "access_key": "YOUR_ACCESS_KEY",
  "secret_key": "YOUR_SECRET_KEY",
  "bucket_name": "your-bucket",
  "prefix": "folder/",
  "recursive": true,
  "animated_progress": true
}
```

### 3. Test First (Safe)
Always start with a dry run to see what would be changed:
```bash
python s3_public_manager.py --config config.json --dry-run
```

### 4. Make Files Public
If the dry run looks correct, proceed with the actual operation:
```bash
python s3_public_manager.py --config config.json
```

## 🎯 **Progress Display Preview**

### With Rich Library (Enhanced)


https://github.com/user-attachments/assets/b350539e-777d-4360-b34a-11597005fbe1




### Without Rich (Simple)
```
File: photo_001.jpg
⠙ [██████████████░░░░░░░░░░░] 245/542 (45.2%)
✓240 ✗1 | Time: 45s | Rate: 5.3/s
```

## 🌐 **Supported Services**

| Service | Configuration | Regions |
|---------|---------------|---------|
| **AWS S3** | `--service aws` | `us-east-1`, `us-west-2`, `eu-west-1`, `ap-southeast-1` |
| **DigitalOcean Spaces** | `--service digitalocean` | `nyc3`, `ams3`, `sgp1`, `fra1`, `sfo3`, `tor1`, `blr1` |
| **Wasabi** | `--service wasabi` | `us-east-1`, `us-east-2`, `us-west-1`, `eu-central-1`, `ap-northeast-1` |
| **Backblaze B2** | `--service backblaze` | `us-west-002`, `eu-central-003` |
| **MinIO** | `--service minio` | `us-east-1` (localhost) |
| **Custom** | `--service custom` | Specify with `--endpoint-url` |

## 📋 **Usage Examples**

### Configuration File Method (Recommended)
```bash
# Create and edit config file
python s3_public_manager.py --create-config
# Use configuration file
python s3_public_manager.py --config config.json


https://github.com/user-attachments/assets/685d7a07-2a30-4f72-9893-4d25e959cec5

```

### Command Line Method
```bash
python s3_public_manager.py \
  --service digitalocean \
  --region fra1 \
  --bucket my-bucket \
  --prefix "images/" \
  --access-key YOUR_KEY \
  --secret-key YOUR_SECRET \
  --animated-progress
```

### Advanced Examples
```bash
# List available buckets
python s3_public_manager.py --config config.json --list-buckets

# Process only direct files (no subdirectories)
python s3_public_manager.py --config config.json --no-recursive

# Disable animated progress
python s3_public_manager.py --config config.json --no-animated-progress

# Verbose logging for debugging
python s3_public_manager.py --config config.json --verbose
```

## ⚙️ **Configuration Options**

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--config` | Path to JSON configuration file | - |
| `--service` | Storage service (`aws`, `digitalocean`, `wasabi`, `backblaze`, `minio`, `custom`) | - |
| `--region` | Service region | - |
| `--bucket` | Bucket name | - |
| `--prefix` | Object prefix/folder path | `""` (root) |
| `--access-key` | Access key ID | - |
| `--secret-key` | Secret access key | - |
| `--endpoint-url` | Custom endpoint URL | - |
| `--recursive` | Include subdirectories | `true` |
| `--no-recursive` | Only process direct files | - |
| `--dry-run` | Preview changes without applying | `false` |
| `--animated-progress` | Enable animated progress display | `true` |
| `--no-animated-progress` | Disable animated progress | - |
| `--list-buckets` | List available buckets | - |
| `--verbose` | Enable detailed logging | - |
| `--create-config` | Create sample configuration file | - |

### Environment Variables

You can also use environment variables for credentials:
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

### JSON Configuration

Complete configuration file example:
```json
{
  "service": "digitalocean",
  "region": "fra1",
  "access_key": "DO00VZEVU7WC2BWAM3Q3",
  "secret_key": "your_secret_key",
  "bucket_name": "my-bucket",
  "prefix": "public-files/",
  "recursive": true,
  "endpoint_url": null,
  "animated_progress": true
}
```

## 🔐 **Security Considerations**

- **Credentials**: Never commit configuration files with real credentials to version control
- **Public Access**: Files made public will be accessible to anyone with the URL
- **Testing**: Always use `--dry-run` first to preview changes
- **Permissions**: Ensure your credentials have the necessary S3 permissions

## 🐛 **Troubleshooting**

### Common Issues

**"Missing required parameters" error:**
```bash
# Make sure all required parameters are provided
python s3_public_manager.py --help
```

**No objects found:**
```bash
# Check your prefix and bucket name
python s3_public_manager.py --config config.json --list-buckets --verbose
```

**Progress display issues:**
```bash
# Install rich for better display or disable animation
pip install rich
# OR
python s3_public_manager.py --config config.json --no-animated-progress
```

### Debug Mode
```bash
python s3_public_manager.py --config config.json --verbose --dry-run
```

## 📄 **License**

MIT License - see LICENSE file for details.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Author:** Daniele Caluri  
**Website:** [caluri.it](https://caluri.it)  
**Version:** 1.1.0
