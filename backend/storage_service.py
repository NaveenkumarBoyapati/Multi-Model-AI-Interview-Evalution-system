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

_PLACEHOLDER_VALUES = {
    "", "none", "null", "undefined", "value", "placeholder",
    "your_cloudflare_account_id", "your_r2_access_key_id",
    "your_r2_secret_access_key", "your_bucket_name",
    "your_password", "gsk_your_groq_api_key_here"
}

_S3_CLIENT = None
_LAST_CONFIG_HASH = None


def get_r2_config() -> Dict[str, str]:
    """Dynamically reads R2 configuration from environment."""
    return {
        "account_id": os.getenv("R2_ACCOUNT_ID", "").strip(),
        "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "").strip(),
        "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "").strip(),
        "bucket_name": os.getenv("R2_BUCKET_NAME", "").strip(),
        "public_url": os.getenv("R2_PUBLIC_URL", "").strip().rstrip("/")
    }


def is_r2_configured() -> bool:
    """Returns True only if all required Cloudflare R2 credentials are set and not placeholder values."""
    cfg = get_r2_config()
    acc = cfg["account_id"]
    key = cfg["access_key_id"]
    secret = cfg["secret_access_key"]
    bucket = cfg["bucket_name"]

    if not (acc and key and secret and bucket):
        return False

    for v in (acc, key, secret, bucket):
        low = v.lower()
        if low in _PLACEHOLDER_VALUES or low.startswith("your_"):
            return False

    return True


def get_s3_client():
    """Initializes and caches a boto3 S3 client for Cloudflare R2."""
    global _S3_CLIENT, _LAST_CONFIG_HASH

    if not is_r2_configured():
        return None

    cfg = get_r2_config()
    current_hash = (cfg["account_id"], cfg["access_key_id"], cfg["secret_access_key"], cfg["bucket_name"])

    if _S3_CLIENT is not None and _LAST_CONFIG_HASH == current_hash:
        return _S3_CLIENT

    try:
        import boto3
        from botocore.config import Config

        endpoint = f"https://{cfg['account_id']}.r2.cloudflaredstorage.com"
        boto_config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=15,
            read_timeout=60
        )

        _S3_CLIENT = boto3.client(
            service_name="s3",
            endpoint_url=endpoint,
            aws_access_key_id=cfg["access_key_id"],
            aws_secret_access_key=cfg["secret_access_key"],
            region_name="auto",
            config=boto_config
        )
        _LAST_CONFIG_HASH = current_hash
        print(f"[Storage Service] Cloudflare R2 client initialized for bucket: {cfg['bucket_name']}")
        return _S3_CLIENT
    except Exception as exc:
        print(f"[Storage Service Warning] Could not initialize boto3 R2 client: {exc}")
        _S3_CLIENT = None
        return None


def generate_presigned_upload_url(
    object_key: str,
    content_type: str = "video/webm",
    expires_in: int = 900
) -> Dict[str, Any]:
    """
    Generates a secure, short-lived presigned PUT URL for direct browser-to-Cloudflare-R2 uploads.
    The browser can PUT the binary WebM blob directly to this URL with upload progress tracking,
    completely bypassing Vercel and Render request body limits.
    """
    if not is_r2_configured():
        return {
            "success": False,
            "error": "Cloudflare R2 is not configured. Missing required credentials.",
            "r2_configured": False
        }

    client = get_s3_client()
    if not client:
        return {
            "success": False,
            "error": "Failed to initialize R2 storage client.",
            "r2_configured": False
        }

    cfg = get_r2_config()
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

        public_url = f"{cfg['public_url']}/{object_key}" if cfg["public_url"] else None

        print(f"[Storage Service] Generated presigned PUT URL for key: {object_key} (expires in {expires_in}s)")
        return {
            "success": True,
            "r2_configured": True,
            "upload_url": presigned_url,
            "object_key": object_key,
            "bucket": bucket,
            "content_type": content_type,
            "expires_in": expires_in,
            "public_url": public_url
        }
    except Exception as exc:
        print(f"[Storage Service Error] Failed to generate presigned upload URL for {object_key}: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "r2_configured": True
        }


def verify_object_in_storage(object_key: str) -> Dict[str, Any]:
    """
    Verifies that an uploaded recording exists in Cloudflare R2 and has valid content.
    Returns metadata dict with exists=True, size_bytes, content_type, etag.
    """
    if not is_r2_configured():
        return {
            "exists": False,
            "size_bytes": 0,
            "error": "Cloudflare R2 is not configured."
        }

    client = get_s3_client()
    if not client:
        return {
            "exists": False,
            "size_bytes": 0,
            "error": "R2 storage client unavailable."
        }

    cfg = get_r2_config()
    bucket = cfg["bucket_name"]

    try:
        head = client.head_object(Bucket=bucket, Key=object_key)
        size_bytes = int(head.get("ContentLength", 0))
        content_type = head.get("ContentType", "video/webm")
        etag = str(head.get("ETag", "")).strip('"')

        if size_bytes <= 0:
            print(f"[Storage Service Warning] Object '{object_key}' exists in R2 but is empty (0 bytes).")
            return {
                "exists": False,
                "size_bytes": 0,
                "error": f"Object '{object_key}' in R2 is empty (0 bytes)."
            }

        print(f"[Storage Service] Verified object in R2: {object_key} ({size_bytes} bytes, {content_type})")
        return {
            "exists": True,
            "size_bytes": size_bytes,
            "content_type": content_type,
            "etag": etag,
            "bucket": bucket,
            "key": object_key
        }
    except Exception as exc:
        print(f"[Storage Service Notice] Object '{object_key}' head check failed in R2: {exc}")
        return {
            "exists": False,
            "size_bytes": 0,
            "error": str(exc)
        }


def download_file_from_storage(object_key: str, destination_path: str) -> bool:
    """
    Downloads an object from Cloudflare R2 to a local file path on disk.
    Used by backend to retrieve recordings from R2 for Whisper transcription.
    """
    client = get_s3_client()
    if not client:
        return False

    cfg = get_r2_config()
    bucket = cfg["bucket_name"]

    try:
        os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
        client.download_file(bucket, object_key, destination_path)
        if os.path.exists(destination_path) and os.path.getsize(destination_path) > 0:
            print(f"[Storage Service] Downloaded R2 object '{object_key}' -> {destination_path} ({os.path.getsize(destination_path)} bytes)")
            return True
        return False
    except Exception as exc:
        print(f"[Storage Service Error] Failed to download {object_key} from R2: {exc}")
        return False


def get_presigned_download_url(object_key: str, expires_in: int = 3600) -> Optional[str]:
    """Generates a secure, short-lived presigned GET URL for recording playback."""
    client = get_s3_client()
    if not client:
        return None

    cfg = get_r2_config()
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
    """Returns public URL if available, else generates a presigned GET URL."""
    cfg = get_r2_config()
    if cfg["public_url"]:
        return f"{cfg['public_url']}/{object_key}"
    return get_presigned_download_url(object_key, expires_in=expires_in)


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
    cfg = get_r2_config()
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

            public_url = f"{cfg['public_url']}/{object_key}" if cfg["public_url"] else None
            print(f"[Storage Service] Uploaded to Cloudflare R2: {object_key} ({bucket})")
            return {
                "success": True,
                "storage": "r2",
                "bucket": bucket,
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
    """Retrieves file bytes from Cloudflare R2."""
    client = get_s3_client()
    cfg = get_r2_config()
    bucket = cfg["bucket_name"]

    if client and bucket:
        try:
            response = client.get_object(Bucket=bucket, Key=object_key)
            return response["Body"].read()
        except Exception as exc:
            print(f"[Storage Service Error] Failed to read {object_key} from R2: {exc}")
            return None
    return None
