import os
from google.cloud import storage
from dotenv import load_dotenv

# Try loading from the new 'keys' directory first (one level up)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'keys', '.env')
if not os.path.exists(dotenv_path):
    # Fallback for Docker or when run from root
    dotenv_path = os.path.join(os.getcwd(), 'keys', '.env')

load_dotenv(dotenv_path)

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "garden-app-bucket")

def upload_to_gcs(file_content: bytes, destination_blob_name: str):
    """Uploads a blob to the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(file_content)
        
        return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        # Return a mock URL for local testing if GCS is not configured
        return f"mock_url://{GCS_BUCKET_NAME}/{destination_blob_name}"

def download_from_gcs(source_blob_name: str):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(source_blob_name)
    return blob.download_as_bytes()
