"""
Custom storage backends for Cloudflare R2.
"""
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class R2MediaStorage(S3Boto3Storage):
    """
    Cloudflare R2 storage backend for media files.
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'
    
    @property
    def bucket_name(self):
        return settings.CLOUDFLARE_R2_BUCKET_NAME
    
    @property
    def custom_domain(self):
        return settings.CLOUDFLARE_R2_PUBLIC_URL
    
    @property
    def endpoint_url(self):
        return settings.CLOUDFLARE_R2_ENDPOINT


class R2StaticStorage(S3Boto3Storage):
    """
    Cloudflare R2 storage backend for static files.
    """
    location = 'static'
    default_acl = 'public-read'
    
    @property
    def bucket_name(self):
        return settings.CLOUDFLARE_R2_BUCKET_NAME
    
    @property
    def custom_domain(self):
        return settings.CLOUDFLARE_R2_PUBLIC_URL
    
    @property
    def endpoint_url(self):
        return settings.CLOUDFLARE_R2_ENDPOINT
