from typing import Optional, BinaryIO
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from qdra.infrastructure.storage.image_storage_provider import ImageStorageProvider


class S3ImageStorageProvider:
    """S3-compatible storage implementation of ImageStorageProvider."""
    
    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        public_base_url: Optional[str] = None,
        force_path_style: bool = False,
    ):
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.public_base_url = public_base_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        
        config = None
        if force_path_style:
            config = Config(s3={'addressing_style': 'path'})
        
        self.s3_client = boto3.client(
            's3',
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=config,
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create the bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                self.s3_client.create_bucket(Bucket=self.bucket)
            else:
                raise
    
    async def save(
        self,
        storage_key: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        """Save image content to S3."""
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=storage_key,
            Body=content,
            ContentType=mime_type,
        )
    
    async def delete(self, storage_key: str) -> None:
        """Delete image from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=storage_key,
            )
        except ClientError:
            pass  # Object may not exist
    
    async def get_public_url(self, storage_key: str) -> Optional[str]:
        """Get public URL for the image if available."""
        if self.public_base_url:
            return f"{self.public_base_url}/{self.bucket}/{storage_key}"
        return None
    
    async def open_read_stream(self, storage_key: str) -> BinaryIO:
        """Open a read stream for the image."""
        response = self.s3_client.get_object(
            Bucket=self.bucket,
            Key=storage_key,
        )
        return response['Body']
    
    async def create_presigned_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Create a presigned URL for uploading an image."""
        # Use public endpoint for presigned URLs if available
        endpoint_url = self.public_base_url or self.endpoint_url
        
        # Create a temporary client with the public endpoint for presigned URL generation
        config = None
        if self.endpoint_url and self.endpoint_url.startswith('http://') and 'minio' in self.endpoint_url:
            # Force path style for MinIO
            config = Config(s3={'addressing_style': 'path'})
        
        temp_client = boto3.client(
            's3',
            region_name=self.region,
            endpoint_url=endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=config,
        )
        
        presigned_url = temp_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket,
                'Key': storage_key,
                'ContentType': content_type,
            },
            ExpiresIn=expires_in_seconds,
        )
        
        # For MinIO with path style, ensure the URL has the correct format
        if endpoint_url and 'minio' in endpoint_url:
            # Replace virtual-hosted style with path style if needed
            if f'://{self.bucket}.' in presigned_url:
                presigned_url = presigned_url.replace(f'://{self.bucket}.', f'://')
                presigned_url = presigned_url.replace(f'{self.bucket}/', '')
                # Insert bucket after the host
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(presigned_url)
                new_path = f'/{self.bucket}{parsed.path}'
                presigned_url = urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))
        
        return presigned_url
    
    async def create_presigned_download_url(
        self,
        storage_key: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Create a presigned URL for downloading an image."""
        # Use public endpoint for presigned URLs if available
        endpoint_url = self.public_base_url or self.endpoint_url
        
        # Create a temporary client with the public endpoint for presigned URL generation
        config = None
        if self.endpoint_url and self.endpoint_url.startswith('http://') and 'minio' in self.endpoint_url:
            # Force path style for MinIO
            config = Config(s3={'addressing_style': 'path'})
        
        temp_client = boto3.client(
            's3',
            region_name=self.region,
            endpoint_url=endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=config,
        )
        
        presigned_url = temp_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': storage_key,
            },
            ExpiresIn=expires_in_seconds,
        )
        
        # For MinIO with path style, ensure the URL has the correct format
        if endpoint_url and 'minio' in endpoint_url:
            # Replace virtual-hosted style with path style if needed
            if f'://{self.bucket}.' in presigned_url:
                presigned_url = presigned_url.replace(f'://{self.bucket}.', f'://')
                presigned_url = presigned_url.replace(f'{self.bucket}/', '')
                # Insert bucket after the host
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(presigned_url)
                new_path = f'/{self.bucket}{parsed.path}'
                presigned_url = urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))
        
        return presigned_url
    
    async def object_exists(self, storage_key: str) -> bool:
        """Check if an object exists in storage."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket,
                Key=storage_key,
            )
            return True
        except ClientError:
            return False
