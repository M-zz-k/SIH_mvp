"""
storage.py
Upload/download evidence images and reports to the Supabase bucket.

Rule for the whole team: never write evidence images to local disk.
Always go through upload_bytes()/download_bytes() here, and always
hash bytes with hashing.hash_bytes() BEFORE calling upload_bytes(),
saving that hash in EvidenceImage.file_hash / Report.evidence_hash.

Supabase Storage speaks the S3 protocol, so this uses boto3 against
the S3-compatible endpoint from Settings -> Storage -> S3 Connection.
"""

import os
import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "evidence-images")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION", "ap-south-1")

_missing = [
    name
    for name, val in [
        ("S3_ENDPOINT_URL", S3_ENDPOINT_URL),
        ("S3_ACCESS_KEY_ID", S3_ACCESS_KEY_ID),
        ("S3_SECRET_ACCESS_KEY", S3_SECRET_ACCESS_KEY),
    ]
    if not val
]
if _missing:
    raise RuntimeError(
        f"Missing storage env vars: {', '.join(_missing)}. "
        "Fill these in .env from Supabase Settings -> Storage -> S3 Connection."
    )

_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name=S3_REGION,
)


def build_key(inspection_id: int, original_filename: str, prefix: str = "evidence") -> str:
    """
    Builds a unique, collision-proof storage key, e.g.:
    evidence/inspection_42/20260910-143210-9c2f1e-label.jpg
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    unique = uuid.uuid4().hex[:8]
    safe_name = original_filename.replace(" ", "_")
    return f"{prefix}/inspection_{inspection_id}/{timestamp}-{unique}-{safe_name}"


def upload_bytes(data: bytes, key: str, content_type: Optional[str] = None) -> str:
    """
    Uploads raw bytes to the bucket at `key`. Returns the key (file_path)
    to store on EvidenceImage.file_path / Report.file_path.

    Always hash `data` with hashing.hash_bytes(data) BEFORE calling this,
    and save that hash alongside the record.
    """
    extra_args = {"ContentType": content_type} if content_type else {}
    _client.put_object(Bucket=BUCKET_NAME, Key=key, Body=data, **extra_args)
    return key


def download_bytes(key: str) -> bytes:
    """Downloads and returns the raw bytes stored at `key`."""
    response = _client.get_object(Bucket=BUCKET_NAME, Key=key)
    return response["Body"].read()


def delete_object(key: str) -> None:
    """Deletes the object at `key`. Use sparingly — evidence should usually be kept."""
    _client.delete_object(Bucket=BUCKET_NAME, Key=key)


def object_exists(key: str) -> bool:
    """Checks whether an object exists at `key` without downloading it."""
    try:
        _client.head_object(Bucket=BUCKET_NAME, Key=key)
        return True
    except _client.exceptions.ClientError:
        return False
