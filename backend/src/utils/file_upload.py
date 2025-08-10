"""
File Upload Service - Handle file uploads for return photos
Supports local storage and cloud storage (S3)
"""
import os
import uuid
import aiofiles
from typing import Optional
import boto3
from datetime import datetime

class FileUploadService:
    """Service for handling file uploads"""
    
    def __init__(self):
        self.storage_mode = os.environ.get('STORAGE_MODE', 'local')  # local, s3
        self.upload_dir = os.environ.get('UPLOAD_DIR', '/tmp/uploads')
        self.s3_bucket = os.environ.get('AWS_S3_BUCKET', 'returns-management-uploads')
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        
        if self.storage_mode == 's3':
            self.s3_client = boto3.client('s3')
    
    async def upload_return_photo(
        self, 
        file_content: bytes, 
        filename: str, 
        tenant_id: str
    ) -> str:
        """
        Upload return photo and return URL
        """
        # Validate file size
        if len(file_content) > self.max_file_size:
            raise ValueError("File size exceeds 5MB limit")
        
        # Generate unique filename
        file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
        unique_filename = f"{tenant_id}/returns/{uuid.uuid4()}.{file_extension}"
        
        if self.storage_mode == 'local':
            return await self._upload_local(file_content, unique_filename)
        elif self.storage_mode == 's3':
            return await self._upload_s3(file_content, unique_filename)
        else:
            raise ValueError(f"Unsupported storage mode: {self.storage_mode}")
    
    async def _upload_local(self, file_content: bytes, filename: str) -> str:
        """Upload file to local storage"""
        
        # Ensure directory exists
        full_path = os.path.join(self.upload_dir, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file_content)
        
        # Return URL (in production, this would be served by a web server)
        return f"/uploads/{filename}"
    
    async def _upload_s3(self, file_content: bytes, filename: str) -> str:
        """Upload file to S3"""
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=filename,
                Body=file_content,
                ContentType='image/jpeg'  # Default to jpeg
            )
            
            # Return S3 URL
            return f"https://{self.s3_bucket}.s3.amazonaws.com/{filename}"
            
        except Exception as e:
            raise ValueError(f"S3 upload failed: {str(e)}")
    
    def validate_image_file(self, filename: str, content_type: str) -> bool:
        """Validate if file is a valid image"""
        
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        allowed_content_types = {
            'image/jpeg', 'image/jpg', 'image/png', 
            'image/gif', 'image/webp'
        }
        
        # Check extension
        file_extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_extension not in allowed_extensions:
            return False
        
        # Check content type
        if content_type not in allowed_content_types:
            return False
        
        return True