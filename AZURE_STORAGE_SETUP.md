# Azure Blob Storage Migration Guide

## Overview

The Flask application has been migrated to use **Azure Blob Storage** for all file operations, preventing crashes caused by heavy files stored locally within the app directory.

### What Changed

**Before:**
- Temporary files stored in `/tmp/simulation_results/`
- User results stored in `hsim/GSOM/flask/static/user_results/{username}/`
- Global leaderboard in `hsim/GSOM/flask/static/results/results.csv`
- Files could fill up disk space and cause crashes

**After:**
- All files stored in Azure Blob Storage containers
- No local filesystem dependencies (except for fallback mode)
- Scalable, reliable cloud storage
- Automatic cleanup of old temporary files

## Azure Blob Storage Architecture

### Container Structure

The application uses three containers in Azure Blob Storage:

1. **`temp-files`** - Temporary simulation files
   - Excel result files: `{username}_{uuid}.xlsx`
   - Gantt charts: `{username}_{uuid}.html`
   - Uploaded input files: `{username}_{uuid}_{original_filename}`
   - **Auto-cleanup**: Files older than 24 hours are automatically removed

2. **`user-results`** - Persistent user results
   - Path structure: `{username}/{filename}.xlsx`
   - Supports versioning: `{filename} v2.xlsx`, `{filename} v3.xlsx`, etc.
   - User-specific organization

3. **`global-results`** - Shared data (future use)
   - Leaderboard CSV files
   - Global statistics

## Setup Instructions

### 1. Create Azure Storage Account

#### Using Azure Portal:

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"** > **"Storage account"**
3. Fill in the details:
   - **Resource group**: Create new or use existing
   - **Storage account name**: Choose a unique name (e.g., `hsimstorageaccount`)
   - **Region**: Choose closest to your deployment
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally Redundant Storage) is sufficient for dev/test
4. Click **"Review + Create"** and then **"Create"**

#### Using Azure CLI:

```bash
# Login to Azure
az login

# Create resource group
az group create --name hsim-resource-group --location eastus

# Create storage account
az storage account create \
  --name hsimstorageaccount \
  --resource-group hsim-resource-group \
  --location eastus \
  --sku Standard_LRS

# Get connection string
az storage account show-connection-string \
  --name hsimstorageaccount \
  --resource-group hsim-resource-group \
  --output table
```

### 2. Get Connection String

#### From Azure Portal:

1. Navigate to your Storage Account
2. Go to **"Access keys"** under **"Security + networking"**
3. Click **"Show keys"**
4. Copy **"Connection string"** from key1 or key2

It will look like:
```
DefaultEndpointsProtocol=https;AccountName=hsimstorageaccount;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net
```

### 3. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Azure Storage connection string:
   ```env
   # Azure Blob Storage Configuration
   AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=hsimstorageaccount;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net

   # Enable Azure Blob Storage
   USE_AZURE_STORAGE=True
   ```

3. **Important**: Add `.env` to `.gitignore` if not already present:
   ```bash
   echo ".env" >> .gitignore
   ```

### 4. Install Dependencies

Update your Python environment with the new Azure SDK:

```bash
pip install -r requirements.txt
```

This will install `azure-storage-blob>=12.19.0`.

### 5. Initialize Containers

The application automatically creates the required containers on startup:
- `temp-files`
- `user-results`
- `global-results`

You can verify this by:
1. Going to Azure Portal > Your Storage Account > **"Containers"**
2. You should see the three containers listed

### 6. Test the Setup

1. Start the Flask application:
   ```bash
   cd hsim/GSOM/flask
   python app.py
   ```

2. Check the logs for confirmation:
   ```
   Azure Blob Storage enabled and initialized
   Created container: temp-files
   Created container: user-results
   Created container: global-results
   ```

3. Test file upload/simulation workflow in the web interface

## Fallback to Local Storage

If you want to temporarily disable Azure Blob Storage and use local filesystem:

1. Edit `.env`:
   ```env
   USE_AZURE_STORAGE=False
   ```

2. Restart the application

The app will automatically fall back to local filesystem storage.

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage connection string | - | Yes (if USE_AZURE_STORAGE=True) |
| `USE_AZURE_STORAGE` | Enable/disable Azure storage | `True` | No |
| `USE_GANTT` | Enable Gantt chart generation | `True` | No |
| `TIMEOUT` | Simulation timeout (seconds) | `180` | No |

### Container Lifecycle

**Automatic Cleanup:**
- Temp files older than 24 hours are automatically removed
- Can be configured in `azure_storage.py` by calling `cleanup_old_temp_files(hours=24)`

**Manual Cleanup:**

You can add a scheduled task or cron job to clean up old files:

```python
from hsim.GSOM.flask.azure_storage import get_storage

# Clean up files older than 12 hours
storage = get_storage()
storage.cleanup_old_temp_files(hours=12)
```

## Cost Estimation

Azure Blob Storage pricing (as of 2025, US East region):

- **Storage**: ~$0.018 per GB/month
- **Operations**:
  - Write: $0.05 per 10,000 operations
  - Read: $0.004 per 10,000 operations

**Example Cost for 100 Users:**
- 100 users × 10 files/user × 2 MB/file = 2 GB storage
- ~$0.036/month storage + minimal operation costs
- **Total: < $1/month for typical usage**

## Security Best Practices

### 1. Use Managed Identity (Production)

For production deployments on Azure (App Service, VM, etc.):

```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Use managed identity instead of connection string
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url="https://hsimstorageaccount.blob.core.windows.net",
    credential=credential
)
```

Update `azure_storage.py` to support this method.

### 2. Use SAS Tokens for Temporary Access

For sharing files with users:

```python
from datetime import datetime, timedelta
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

# Generate temporary download link (1 hour expiry)
sas_token = generate_blob_sas(
    account_name="hsimstorageaccount",
    container_name="user-results",
    blob_name=f"{username}/{filename}",
    account_key=account_key,
    permission=BlobSasPermissions(read=True),
    expiry=datetime.utcnow() + timedelta(hours=1)
)

download_url = f"https://hsimstorageaccount.blob.core.windows.net/user-results/{username}/{filename}?{sas_token}"
```

### 3. Network Security

Configure firewall rules in Azure Portal:
- **Storage Account** > **Networking**
- Add your IP addresses or Azure VNet
- Enable "Secure transfer required" (HTTPS only)

## Monitoring and Troubleshooting

### Enable Diagnostic Logging

In Azure Portal:
1. Go to your Storage Account
2. **Monitoring** > **Diagnostic settings**
3. Add diagnostic setting:
   - Enable **Blob logs**
   - Send to **Log Analytics workspace**

### Common Issues

#### Issue: "Azure Blob Storage not initialized"

**Solution**: Check that `AZURE_STORAGE_CONNECTION_STRING` is set correctly in `.env`

```bash
# Verify connection string
python -c "from hsim.GSOM.flask.config import AZURE_STORAGE_CONNECTION_STRING; print('OK' if AZURE_STORAGE_CONNECTION_STRING else 'NOT SET')"
```

#### Issue: "Container not found"

**Solution**: Containers are auto-created on first run. If manually deleted, restart the app to recreate them.

#### Issue: Slow file operations

**Solution**:
- Ensure storage account is in the same region as your deployment
- Check Azure status page for service issues
- Consider upgrading to Premium performance tier

#### Issue: Connection timeout

**Solution**:
```python
# Increase timeout in azure_storage.py
blob_client.upload_blob(data, timeout=300)  # 5 minutes
```

### View Storage Metrics

Use Azure Storage Explorer or Azure Portal:
- **Storage Account** > **Monitoring** > **Metrics**
- Monitor: Transactions, Ingress, Egress, Latency

## Migration from Local Storage

If you have existing files in local storage, migrate them to Azure:

```python
import os
from hsim.GSOM.flask.azure_storage import get_storage

storage = get_storage()

# Migrate user results
base_folder = "hsim/GSOM/flask/static/user_results"
for username in os.listdir(base_folder):
    user_folder = os.path.join(base_folder, username)
    if os.path.isdir(user_folder):
        for filename in os.listdir(user_folder):
            if filename.endswith('.xlsx'):
                filepath = os.path.join(user_folder, filename)
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                    storage.upload_file(
                        file_data,
                        filename,
                        storage.USER_RESULTS_CONTAINER,
                        username
                    )
                print(f"Migrated: {username}/{filename}")
```

## Advanced Configuration

### Custom Container Names

Edit [azure_storage.py](hsim/GSOM/flask/azure_storage.py):

```python
class AzureBlobStorage:
    TEMP_CONTAINER = "my-temp-files"
    USER_RESULTS_CONTAINER = "my-user-results"
    GLOBAL_RESULTS_CONTAINER = "my-global-results"
```

### Add Lifecycle Management

In Azure Portal > Storage Account > Data management > Lifecycle management:

```json
{
  "rules": [
    {
      "name": "DeleteOldTempFiles",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["temp-files/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 1
            }
          }
        }
      }
    }
  ]
}
```

This automatically deletes temp files older than 1 day.

## API Reference

See [azure_storage.py](hsim/GSOM/flask/azure_storage.py) for the complete API.

### Key Methods

```python
from hsim.GSOM.flask.azure_storage import get_storage

storage = get_storage()

# Upload file
storage.upload_file(file_data, filename, container, username=None)

# Download file
file_data = storage.download_file(filename, container, username=None)

# Download as stream (for Flask send_file)
stream = storage.download_file_stream(filename, container, username=None)

# Delete file
storage.delete_file(filename, container, username=None)

# Rename file
storage.rename_file(old_name, new_name, container, username=None)

# List user files
files = storage.list_user_files(username, container=None)

# Check if file exists
exists = storage.file_exists(filename, container, username=None)

# Clean up old temp files
storage.cleanup_old_temp_files(hours=24)
```

## Support

For issues or questions:
- Check logs: Look for errors in Flask application logs
- Azure Portal: Check Storage Account metrics and logs
- GitHub Issues: Report bugs at your repository

## References

- [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)
- [Azure Storage Explorer](https://azure.microsoft.com/features/storage-explorer/)
