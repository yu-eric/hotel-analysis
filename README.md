# Distributed Hotel Review Sentiment Analysis Pipeline

A scalable data pipeline for performing sentiment analysis on hotel reviews using Dask, Dagster, and machine learning transformers. This project demonstrates distributed computing patterns, workflow orchestration, and ETL pipeline design for processing large datasets.

## 🚀 Features

- **Distributed Computing**: Leverages Dask for parallel processing of large CSV datasets
- **Workflow Orchestration**: Uses Dagster for managing data pipeline assets and dependencies
- **ML-Powered Analysis**: Employs HuggingFace transformers for sentiment analysis (RoBERTa model)
- **Multi-Storage Backend**: Supports both S3-compatible storage (MinIO) and PostgreSQL
- **Infrastructure as Code**: Complete Terraform configuration for reproducible deployments
- **Automated Provisioning**: Ansible playbooks for configuration management

## 📋 Architecture

The pipeline consists of:
- **1 Host Node**: Runs MinIO (S3-compatible storage) and Dask scheduler
- **4 Worker Nodes**: Execute Dask workers and host the Dagster orchestrator
- **Data Flow**: CSV → Dask processing → Sentiment analysis → Output (Parquet/PostgreSQL)

## 🛠️ Prerequisites

- Terraform >= 1.0
- Python >= 3.8
- Ansible (for automated deployment)
- Access to a virtualization platform (configured for Harvester in this project)

## 📦 Installation & Setup

### 1. Configure Variables

Edit `variables.tf` to match your environment:

```terraform
variable "namespace" {
  default = "your-namespace"
}

variable "network_name" {
  default = "your-namespace/your-network"
}

variable "username" {
  default = "your-username"
}

variable "keyname" {
  default = "your-ssh-key-name"
}
```

### 2. Provision Infrastructure

```bash
terraform init
terraform apply
```

### 3. Deploy Application Stack

Update `deploy.sh` with your repository path:

```bash
REPO_DIR="/path/to/your/cloned/repo"
```

Then execute:

```bash
./deploy.sh
```

**Note**: If you encounter connection errors, wait a few minutes for the VMs to complete initialization, then retry.

## 📊 Usage

### Accessing Dashboards

Once deployed, you can access:

- **Dask Dashboard**: Monitor distributed task execution and worker resources at `https://your-dask-endpoint/`
- **Dagster UI**: Manage pipeline assets and runs at `https://your-dagster-endpoint/`
- **MinIO Console**: Manage S3 buckets and files at `https://your-minio-endpoint/` (default credentials: `minioadmin`/`minioadmin`)

### Running the Pipeline

#### Default Dataset (500k reviews)

1. Navigate to Dagster UI → Assets page
2. Select all assets using checkboxes
3. Click "Materialize selected" (or "Materialize all" in graph view)
4. Monitor progress in the Runs tab

#### Custom Dataset

1. Upload your CSV file to the MinIO `dask` bucket (ensure it follows the same schema)
2. In Dagster UI → Assets, select only the `input_file` asset
3. Click dropdown → "Open launchpad"
4. Change `filename` parameter to your file name (e.g., `test.csv`)
5. Click materialize to save
6. Return to Assets page, select all assets **except** `input_file`
7. Click "Materialize selected"

### Querying Results

#### PostgreSQL Access

SSH into the first worker node and connect to the database:

```bash
psql -d dagster
```

**Sample Queries:**

**Average Positive Sentiment by Nationality:**
```sql
SELECT
    "Reviewer_Nationality",
    AVG("Positive_Score") AS average_positive_score,
    COUNT(*) AS number_of_reviews
FROM hotel_reviews
WHERE "Positive_Score" IS NOT NULL
GROUP BY "Reviewer_Nationality"
ORDER BY average_positive_score DESC;
```

**Top 10 Hotels by Sentiment:**
```sql
SELECT
    "Hotel_Name",
    AVG("Positive_Score") AS average_reviewer_score,
    COUNT(*) AS number_of_reviews
FROM hotel_reviews
WHERE "Positive_Score" IS NOT NULL
GROUP BY "Hotel_Name"
HAVING COUNT(*) > 10
ORDER BY average_reviewer_score DESC
LIMIT 10;
```

#### Data Schema

| Column Name | Description |
|-------------|-------------|
| `Hotel_Address` | Address of hotel |
| `Review_Date` | Date when review was posted |
| `Average_Score` | Hotel's average score |
| `Hotel_Name` | Name of hotel |
| `Reviewer_Nationality` | Reviewer's nationality |
| `Negative_Review` | Negative review text (or "No Negative") |
| `Review_Total_Negative_Word_Counts` | Word count of negative review |
| `Positive_Review` | Positive review text (or "No Positive") |
| `Review_Total_Positive_Word_Counts` | Word count of positive review |
| `Reviewer_Score` | Score given by reviewer |
| `Total_Number_of_Reviews_Reviewer_Has_Given` | Reviewer's total reviews |
| `Total_Number_of_Reviews` | Hotel's total reviews |
| `Tags` | Review tags |
| `days_since_review` | Days between review and scrape date |
| `Additional_Number_of_Scoring` | Number of scores without reviews |
| `lat` | Hotel latitude |
| `lng` | Hotel longitude |
| `Positive_Score` | **Generated sentiment score for positive review** |
| `Negative_Score` | **Generated sentiment score for negative review** |

## 🔧 Configuration

### Customizing Endpoints

Update S3 endpoints in the following files:
- `benchmark.py`
- `roles/dagster/files/sentiment_analysis/__init__.py`
- `roles/host/tasks/minio.yaml`

### Adjusting Resources

Modify VM specifications in `main.tf`:
- CPU and memory allocation
- Disk sizes
- Number of worker nodes (`vm_count` variable)

## 📁 Project Structure

```
.
├── main.tf                    # Terraform VM definitions
├── variables.tf               # Configuration variables
├── deploy.sh                  # Deployment automation script
├── benchmark.py               # Performance testing script
├── roles/
│   ├── common/               # Common system configuration
│   ├── host/                 # Host node setup (MinIO, Dask scheduler)
│   ├── worker/               # Worker node setup (Dask workers)
│   └── dagster/              # Dagster pipeline definition
│       └── files/
│           └── sentiment_analysis/  # Pipeline code
└── README.md
```

## 🧪 Benchmarking

Run `benchmark.py` to test pipeline performance with different configurations:

```bash
python benchmark.py
```

## 🤝 Contributing

This project was developed as a demonstration of distributed data engineering patterns. Feel free to fork and adapt for your use cases.

## 📄 License

This project is available under the MIT license. See [LICENSE](https://github.com/yu-eric/hotel-analysis/blob/master/LICENSE) for more details.
## 🙏 Acknowledgments

- Dataset: [Hotel Reviews Dataset](https://www.kaggle.com/datasets/jiashenliu/515k-hotel-reviews-data-in-europe)
- Sentiment Model: [cardiffnlp/twitter-roberta-base-sentiment-latest](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest)
