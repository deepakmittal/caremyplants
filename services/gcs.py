import os
from google.cloud import storage
from dotenv import load_dotenv

# Determine environment
IS_CLOUD_RUN = os.getenv('K_SERVICE') is not None

# Try loading from various possible locations for the .env file
dotenv_locations = []
if IS_CLOUD_RUN:
    dotenv_locations.append(os.path.join('/keys', '.env'))

dotenv_locations.extend([
    os.path.join(os.path.dirname(__file__), '..', 'keys', '.env'), # Local dev (one level up)
    os.path.join(os.getcwd(), 'keys', '.env'),                   # Docker /app/keys/
])

for loc in dotenv_locations:
    if os.path.exists(loc):
        load_dotenv(loc)
        break
else:
    load_dotenv() # Fallback to default behavior

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
