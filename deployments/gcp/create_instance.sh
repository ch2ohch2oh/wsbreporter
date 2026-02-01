#!/bin/bash
# Create a free tier GCP Compute Engine instance for wsbreporter
# This script creates an e2-micro instance which is eligible for GCP free tier

set -e

# Configuration
INSTANCE_NAME="wsbreporter-vm"
ZONE="us-east1-b"
MACHINE_TYPE="e2-micro"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
BOOT_DISK_SIZE="10GB"
BOOT_DISK_TYPE="pd-standard"

echo "=== Creating GCP Compute Engine Instance ==="
echo ""
echo "Instance name: $INSTANCE_NAME"
echo "Zone: $ZONE"
echo "Machine type: $MACHINE_TYPE (Free tier eligible)"
echo "Boot disk: $BOOT_DISK_SIZE"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Error: Not authenticated with gcloud"
    echo "Run: gcloud auth login"
    exit 1
fi

# Get current project
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT" ]; then
    echo "Error: No GCP project set"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "Using project: $PROJECT"
echo ""

# Check if instance already exists
if gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE &>/dev/null; then
    echo "Instance $INSTANCE_NAME already exists in zone $ZONE"
    echo ""
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing instance..."
        gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet
    else
        echo "Aborted."
        exit 0
    fi
fi

# Create the instance
echo "Creating instance..."
gcloud compute instances create $INSTANCE_NAME \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --image-family=$IMAGE_FAMILY \
  --image-project=$IMAGE_PROJECT \
  --boot-disk-size=$BOOT_DISK_SIZE \
  --boot-disk-type=$BOOT_DISK_TYPE \
  --metadata=startup-script='#!/bin/bash
# Set timezone to America/New_York
timedatectl set-timezone America/New_York
'

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Instance created successfully!"
    echo ""
    echo "Instance details:"
    gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="table(name,zone,machineType,status,networkInterfaces[0].accessConfigs[0].natIP)"
    echo ""
    echo "Next steps:"
    echo "1. SSH into the instance:"
    echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
    echo ""
    echo "2. Run the bootstrap script:"
    echo "   curl -O https://raw.githubusercontent.com/ch2ohch2oh/wsbreporter/main/deployments/gcp/bootstrap.sh"
    echo "   chmod +x bootstrap.sh"
    echo "   ./bootstrap.sh"
    echo ""
    echo "Free tier info:"
    echo "- e2-micro instances are free for 1 instance per month"
    echo "- 30 GB-months of standard persistent disk storage"
    echo "- More info: https://cloud.google.com/free"
else
    echo ""
    echo "❌ Instance creation failed!"
    exit 1
fi
