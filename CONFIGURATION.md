# Configuration Guide

This guide explains how to configure the project for your specific environment.

## Required Configurations

### 1. Terraform Variables (`variables.tf`)

Update these values before deploying:

```terraform
variable "namespace" {
  default = "your-namespace"  # Your Kubernetes/Harvester namespace
}

variable "network_name" {
  default = "your-namespace/your-network"  # Network in format: namespace/network
}

variable "username" {
  default = "your-username"  # Prefix for VM names
}

variable "keyname" {
  default = "your-ssh-key-name"  # Name of your SSH key in Harvester
}
```

### 2. S3 Endpoint Configuration

Update the S3/MinIO endpoint URL in the following files:

#### `benchmark.py` (line ~46)
```python
config = {"anon": True, "client_kwargs": {"endpoint_url": "https://your-s3-endpoint.example.com"}}
```

#### `roles/dagster/files/sentiment_analysis/__init__.py` (lines ~33, ~83, ~107, ~121)
```python
s3_config = {"anon": True, "client_kwargs": {"endpoint_url": "https://your-s3-endpoint.example.com"}}
```

#### `roles/host/tasks/minio.yaml` (line ~170)
```yaml
command: mc alias set eda2 https://your-s3-endpoint.example.com/ minioadmin minioadmin
```

### 3. Deployment Script (`deploy.sh`)

Update the repository directory path:

```bash
REPO_DIR="/path/to/your/cloned/repo"
```

### 4. Ingress Configuration (Optional)

If you're using an ingress controller/load balancer, uncomment and configure the tags in `main.tf` (lines ~123-145):

```terraform
tags = count.index == 0 ? {
  # Configure your ingress settings here
  ingress_dagster_hostname = "${var.username}-dagster"
  ingress_dagster_port = 3000
  # ... etc
} : {}
```

## Optional Configurations

### Resource Allocation

Adjust VM resources in `main.tf`:

**Host VM** (lines ~46-47):
```terraform
cpu    = 2 
memory = "4Gi"
```

**Worker VMs** (lines ~95-96):
```terraform
cpu    = 4
memory = "32Gi"
```

### Number of Workers

Modify `vm_count` in `variables.tf`:
```terraform
variable "vm_count" {
  default = 4  # Number of worker nodes
}
```

### Dask Configuration

Edit worker configuration in `roles/worker/files/distributed.yaml` to tune:
- Worker threads
- Memory limits
- Spill-to-disk thresholds

### Database Configuration

PostgreSQL connection settings are in `roles/dagster/files/sentiment_analysis/__init__.py`:

```python
class PostgresResource(ConfigurableResource):
    def get_engine() -> Engine:
         return sa.create_engine("postgresql+psycopg:///dagster")
```

## Security Notes

⚠️ **Important**: This configuration uses default MinIO credentials (`minioadmin`/`minioadmin`). For production use:

1. Change MinIO credentials in:
   - `roles/host/tasks/minio.yaml`
   - All S3 config dictionaries (remove `anon: True`, add credentials)

2. Secure your SSH keys and don't commit them to version control

3. Use proper secrets management (HashiCorp Vault, AWS Secrets Manager, etc.)

4. Configure firewall rules and network policies appropriately

## Validation

After configuration, validate your setup:

```bash
# Check Terraform configuration
terraform validate

# Preview changes
terraform plan

# Verify Python syntax
python -m py_compile benchmark.py
python -m py_compile roles/dagster/files/sentiment_analysis/__init__.py
```
