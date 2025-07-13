# S3 Public File

<p align="center">
<img width="600" alt="d216ceb5-47a8-4db3-bb04-bc12122f503f" src="https://github.com/user-attachments/assets/030b6476-a60b-4453-9c55-cff3fdb71b37" />
</p>


Make files public on S3-compatible storage services (AWS S3, DigitalOcean Spaces, Wasabi, etc.)

## ⚠️ **DISCLAIMER**

**USE AT YOUR OWN RISK.** This tool modifies file permissions on your cloud storage. The authors are not responsible for any damages, data loss, security issues, or problems caused by the use of this software. Always test with `--dry-run` first and ensure you understand the implications of making files publicly accessible.

## Installation

```bash
pip install boto3
```

## Quick Start

1. **Create config file:**

```bash
python s3_public_file.py --create-config
```

2. **Edit config.json with your credentials:**

```json
{
  "service": "digitalocean",
  "region": "fra1",
  "access_key": "YOUR_ACCESS_KEY",
  "secret_key": "YOUR_SECRET_KEY",
  "bucket_name": "your-bucket",
  "prefix": "folder/",
  "recursive": true
}
```

3. **Test first (safe):**

```bash
python s3_public_file.py --config config.json --dry-run
```

4. **Make files public:**

```bash
python s3_public_file.py --config config.json
```

## Supported Services

- **AWS S3** - `--service aws`
- **DigitalOcean Spaces** - `--service digitalocean`
- **Wasabi** - `--service wasabi`
- **Backblaze B2** - `--service backblaze`
- **MinIO** - `--service minio`

## Command Line Usage

```bash
python s3_public_file.py \
  --service digitalocean \
  --region fra1 \
  --bucket my-bucket \
  --prefix "images/" \
  --access-key YOUR_KEY \
  --secret-key YOUR_SECRET \
  --dry-run
```

## Options

- `--dry-run` - Preview changes without applying
- `--recursive` - Include subdirectories (default: true)
- `--verbose` - Show detailed output
- `--list-buckets` - Show available buckets

## License

MIT
