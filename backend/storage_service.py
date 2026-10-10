"""
Cloudflare R2 / AWS S3 Persistent Object Storage Service Module.
Provides persistent cloud storage for candidate WebM interview recordings and generated PDF reports.
If R2 credentials are not set, falls back gracefully to local disk storage (backend/uploads/).
"""

import os
import mimetypes
from typing import Optional, Dict, Any

try:
    from env_loader import load_env
except ImportError:
    try:
        from backend.env_loader import load_env
    except ImportError:
        def load_env(override=False):
            return {}

load_env()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "").strip()
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "").strip().rstrip("/")

_S3_CLIENT = None

def is_r2_configured() -> bool:
    """Returns True if all required Cloudflare R2 credentials are set."""
    return bool(R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME)

def get_s3_client():
    global _S3_CLIENT
    if not is_r2_configured():
        return None
    if _S3_CLIENT is None:
        try:
            import boto3
            endpoint = f"https://{R2_ACCOUNT_ID}.r2.cloudflaredstorage.com"
            _S3_CLIENT = boto3.client(
                service_name="s3",
                endpoint_url=endpoint,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name="auto"
            )
            print(f"[Storage Service] Cloudflare R2 client initialized for bucket: {R2_BUCKET_NAME}")
        except Exception as exc:
            print(f"[Storage Service Warning] Could not initialize boto3 R2 client: {exc}")
            _S3_CLIENT = None
    return _S3_CLIENT

def upload_file_to_storage(local_path: str, object_key: str, content_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Uploads a local file to Cloudflare R2 bucket.
    If R2 is not configured, retains file on local filesystem.
    Returns metadata dict with storage type and URL/key.
    """
    if not os.path.exists(local_path):
        return {
            "success": False,
            "storage": "none",
            "error": "Local file not found"
        }

    client = get_s3_client()
    if client and R2_BUCKET_NAME:
        try:
            mime = content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"
            with open(local_path, "rb") as f:
                client.upload_fileobj(
                    f,
                    R2_BUCKET_NAME,
                    object_key,
                    ExtraArgs={"ContentType": mime}
                )
            
            public_url = f"{R2_PUBLIC_URL}/{object_key}" if R2_PUBLIC_URL else None
            print(f"[Storage Service] Uploaded to Cloudflare R2: {object_key} ({R2_BUCKET_NAME})")
            return {
                "success": True,
                "storage": "r2",
                "bucket": R2_BUCKET_NAME,
                "key": object_key,
                "url": public_url
            }
        except Exception as r2_err:
            print(f"[Storage Service Error] Failed uploading {object_key} to R2: {r2_err}. Kept on local disk.")
            return {
                "success": True,
                "storage": "local",
                "path": local_path,
                "warning": str(r2_err)
            }

    # Fallback to local storage
    return {
        "success": True,
        "storage": "local",
        "path": local_path
    }

def get_file_bytes_from_storage(object_key: str) -> Optional[bytes]:
    """
    Retrieves file bytes from Cloudflare R2.
    """
    client = get_s3_client()
    if client and R2_BUCKET_NAME:
        try:
            response = client.get_object(Bucket=R2_BUCKET_NAME, Key=object_key)
            return response["Body"].read()
        except Exception as exc:
            print(f"[Storage Service Error] Failed to read {object_key} from R2: {exc}")
            return None
    return None
