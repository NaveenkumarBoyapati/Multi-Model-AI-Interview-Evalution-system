"""
Amazon Web Services (AWS) S3 Persistent Object Storage Service Module.
Provides persistent cloud storage for candidate WebM interview recordings and generated PDF reports.
Connects to AWS S3 bucket in configured region (ap-south-1) using boto3.
If S3 credentials are not set, falls back gracefully to local disk storage (backend/uploads/).
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

_PLACEHOLDER_VALUES = {
    "", "none", "null", "undefined", "value", "placeholder",
    "your_aws_access_key_id", "your_aws_secret_access_key",
    "your_bucket_name", "your_cloudflare_account_id",
    "your_r2_access_key_id", "your_r2_secret_access_key",
    "your_password", "gsk_your_groq_api_key_here"
}

_S3_CLIENT = None
_LAST_CONFIG_HASH = None


def get_s3_config() -> Dict[str, Any]:
    """
    Dynamically reads AWS S3 configuration from environment variables.
    Primary Render environment variables:
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - AWS_REGION (default: ap-south-1)
      - S3_BUCKET_NAME (default: ai-interview-recordings-nb2026)
    Backward compatibility aliases (R2_*) are supported if present.
    """
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip() or os.getenv("R2_ACCESS_KEY_ID", "").strip()
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip() or os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
    region = os.getenv("AWS_REGION", "").strip() or os.getenv("AWS_DEFAULT_REGION", "").strip() or "ap-south-1"
    bucket = os.getenv("S3_BUCKET_NAME", "").strip() or os.getenv("R2_BUCKET_NAME", "").strip() or "ai-interview-recordings-nb2026"
    endpoint_url = os.getenv("AWS_ENDPOINT_URL", "").strip() or None

    return {
        "access_key_id": access_key,
        "secret_access_key": secret_key,
        "region": region,
        "bucket_name": bucket,
        "endpoint_url": endpoint_url
    }


def is_s3_configured() -> bool:
    """Returns True only if all required AWS S3 credentials are set and not placeholder values."""
    cfg = get_s3_config()
    acc = cfg["access_key_id"]
    secret = cfg["secret_access_key"]
    bucket = cfg["bucket_name"]
    region = cfg["region"]

    if not (acc and secret and bucket and region):
        return False

    for v in (acc, secret, bucket, region):
        low = v.lower()
        if low in _PLACEHOLDER_VALUES or low.startswith("your_"):
            return False

    return True


# Backward-compatibility aliases
def is_r2_configured() -> bool:
    return is_s3_configured()


def get_r2_config() -> Dict[str, Any]:
    cfg = get_s3_config()
    return {
        "account_id": "",
        "access_key_id": cfg["access_key_id"],
        "secret_access_key": cfg["secret_access_key"],
        "bucket_name": cfg["bucket_name"],
        "public_url": "",
        "region": cfg["region"],
        "endpoint_url": cfg["endpoint_url"]
    }


def get_s3_client():
    """Initializes and caches a boto3 S3 client for Amazon S3."""
    global _S3_CLIENT, _LAST_CONFIG_HASH

    if not is_s3_configured():
        return None

    cfg = get_s3_config()
    current_hash = (
        cfg["access_key_id"],
        cfg["secret_access_key"],
        cfg["region"],
        cfg["bucket_name"],
        cfg["endpoint_url"]
    )

    if _S3_CLIENT is not None and _LAST_CONFIG_HASH == current_hash:
        return _S3_CLIENT

    try:
        import boto3
        from botocore.config import Config

        boto_config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=15,
            read_timeout=60,
            s3={"addressing_style": "virtual"}
        )

        client_kwargs = {
            "service_name": "s3",
            "region_name": cfg["region"],
            "aws_access_key_id": cfg["access_key_id"],
            "aws_secret_access_key": cfg["secret_access_key"],
            "config": boto_config
        }
        if cfg["endpoint_url"]:
            client_kwargs["endpoint_url"] = cfg["endpoint_url"]

        _S3_CLIENT = boto3.client(**client_kwargs)
        _LAST_CONFIG_HASH = current_hash
        print(f"[Storage Service] AWS S3 client initialized for bucket: {cfg['bucket_name']} (Region: {cfg['region']})")
        return _S3_CLIENT
    except Exception as exc:
        print(f"[Storage Service Warning] Could not initialize boto3 S3 client: {exc}")
        _S3_CLIENT = None
        return None


def generate_presigned_upload_url(
    object_key: str,
    content_type: str = "video/webm",
    expires_in: int = 900
) -> Dict[str, Any]:
    """
    Generates a secure, short-lived presigned PUT URL for direct browser-to-Amazon-S3 uploads.
    The browser PUTs the binary WebM blob directly to this URL with upload progress tracking,
    completely bypassing Vercel and Render request body limits.
    """
    if not is_s3_configured():
        return {
            "success": False,
            "error": "Amazon S3 is not configured. Missing required AWS credentials.",
            "s3_configured": False,
            "r2_configured": False
        }

    client = get_s3_client()
    if not client:
        return {
            "success": False,
            "error": "Failed to initialize AWS S3 storage client.",
            "s3_configured": False,
            "r2_configured": False
        }

    cfg = get_s3_config()
    bucket = cfg["bucket_name"]

    try:
        params = {
            "Bucket": bucket,
            "Key": object_key,
            "ContentType": content_type
        }
        presigned_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expires_in
        )

        print(f"[Storage Service] Generated presigned PUT URL for key: {object_key} (Bucket: {bucket}, Region: {cfg['region']}, expires in {expires_in}s)")
        return {
            "success": True,
            "s3_configured": True,
            "r2_configured": True,
            "upload_url": presigned_url,
            "object_key": object_key,
            "bucket": bucket,
            "region": cfg["region"],
            "content_type": content_type,
            "expires_in": expires_in
        }
    except Exception as exc:
        print(f"[Storage Service Error] Failed to generate presigned upload URL for {object_key}: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "s3_configured": True,
            "r2_configured": True
        }


def verify_object_in_storage(object_key: str) -> Dict[str, Any]:
    """
    Verifies that an uploaded recording exists in Amazon S3 and has valid content (> 0 bytes).
    Returns metadata dict with exists=True, size_bytes, content_type, etag.
    """
    if not is_s3_configured():
        return {
            "exists": False,
            "size_bytes": 0,
            "error": "Amazon S3 is not configured."
        }

    client = get_s3_client()
    if not client:
        return {
            "exists": False,
            "size_bytes": 0,
            "error": "AWS S3 storage client unavailable."
        }

    cfg = get_s3_config()
    bucket = cfg["bucket_name"]

    try:
        head = client.head_object(Bucket=bucket, Key=object_key)
        size_bytes = int(head.get("ContentLength", 0))
        content_type = head.get("ContentType", "video/webm")
        etag = str(head.get("ETag", "")).strip('"')

        if size_bytes <= 0:
            print(f"[Storage Service Warning] Object '{object_key}' exists in S3 but is empty (0 bytes).")
            return {
                "exists": False,
                "size_bytes": 0,
                "error": f"Object '{object_key}' in S3 is empty (0 bytes)."
            }

        print(f"[Storage Service] Verified object in Amazon S3: {object_key} ({size_bytes} bytes, {content_type})")
        return {
            "exists": True,
            "size_bytes": size_bytes,
            "content_type": content_type,
            "etag": etag,
            "bucket": bucket,
            "key": object_key,
            "region": cfg["region"]
        }
    except Exception as exc:
        print(f"[Storage Service Notice] Object '{object_key}' head check failed in S3: {exc}")
        return {
            "exists": False,
            "size_bytes": 0,
            "error": str(exc)
        }


def download_file_from_storage(object_key: str, destination_path: str) -> bool:
    """
    Downloads an object from Amazon S3 to a local file path on disk.
    Used by backend to retrieve recordings from S3 for Whisper speech-to-text transcription.
    """
    client = get_s3_client()
    if not client:
        return False

    cfg = get_s3_config()
    bucket = cfg["bucket_name"]

    try:
        os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
        client.download_file(bucket, object_key, destination_path)
        if os.path.exists(destination_path) and os.path.getsize(destination_path) > 0:
            print(f"[Storage Service] Downloaded S3 object '{object_key}' -> {destination_path} ({os.path.getsize(destination_path)} bytes)")
            return True
        return False
    except Exception as exc:
        print(f"[Storage Service Error] Failed to download {object_key} from Amazon S3: {exc}")
        return False


def get_presigned_download_url(object_key: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generates a secure, short-lived presigned GET URL for recording playback.
    The S3 bucket remains strictly private with Block Public Access enabled.
    """
    client = get_s3_client()
    if not client:
        return None

    cfg = get_s3_config()
    try:
        url = client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": cfg["bucket_name"], "Key": object_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as exc:
        print(f"[Storage Service Error] Failed to generate download URL for {object_key}: {exc}")
        return None


def get_recording_access_url(object_key: str, expires_in: int = 3600) -> Optional[str]:
    """
    Returns secure, short-lived presigned GET URL for private S3 recording playback.
    """
    return get_presigned_download_url(object_key, expires_in=expires_in)


def upload_file_to_storage(local_path: str, object_key: str, content_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Uploads a local file to Amazon S3 bucket.
    If S3 is not configured, retains file on local filesystem.
    Returns metadata dict with storage type and URL/key.
    """
    if not os.path.exists(local_path):
        return {
            "success": False,
            "storage": "none",
            "error": "Local file not found"
        }

    client = get_s3_client()
    cfg = get_s3_config()
    bucket = cfg["bucket_name"]

    if client and bucket:
        try:
            mime = content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"
            with open(local_path, "rb") as f:
                client.upload_fileobj(
                    f,
                    bucket,
                    object_key,
                    ExtraArgs={"ContentType": mime}
                )

            print(f"[Storage Service] Uploaded to Amazon S3: {object_key} (Bucket: {bucket}, Region: {cfg['region']})")
            return {
                "success": True,
                "storage": "s3",
                "bucket": bucket,
                "region": cfg["region"],
                "key": object_key
            }
        except Exception as s3_err:
            print(f"[Storage Service Error] Failed uploading {object_key} to S3: {s3_err}. Kept on local disk.")
            return {
                "success": True,
                "storage": "local",
                "path": local_path,
                "warning": str(s3_err)
            }

    # Fallback to local storage
    return {
        "success": True,
        "storage": "local",
        "path": local_path
    }


def get_file_bytes_from_storage(object_key: str) -> Optional[bytes]:
    """Retrieves file bytes from Amazon S3."""
    client = get_s3_client()
    cfg = get_s3_config()
    bucket = cfg["bucket_name"]

    if client and bucket:
        try:
            response = client.get_object(Bucket=bucket, Key=object_key)
            return response["Body"].read()
        except Exception as exc:
            print(f"[Storage Service Error] Failed to read {object_key} from S3: {exc}")
            return None
    return None
