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
        return getattr(settings, 'CLOUDFLARE_R2_BUCKET_NAME', '')
    
    @property
    def custom_domain(self):
        return getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', None)
    
    @property
    def endpoint_url(self):
        return getattr(settings, 'CLOUDFLARE_R2_ENDPOINT', '')

    def url(self, name, parameters=None, expire=None):
        """
        Return the full URL directly from settings to avoid double https://
        """
        base_url = getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', '')
        if base_url:
            return f"{base_url}/{self.location}/{name}"
        # Fallback to default behavior
        return super().url(name, parameters, expire)


class R2StaticStorage(S3Boto3Storage):
    """
    Cloudflare R2 storage backend for static files.
    """
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = True
    
    @property
    def bucket_name(self):
        return getattr(settings, 'CLOUDFLARE_R2_BUCKET_NAME', '')
    
    @property
    def custom_domain(self):
        return getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', None)
    
    @property
    def endpoint_url(self):
        return getattr(settings, 'CLOUDFLARE_R2_ENDPOINT', '')

    def url(self, name, parameters=None, expire=None):
        """
        Return the full URL directly from settings to avoid double https://
        """
        base_url = getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', '')
        if base_url:
            return f"{base_url}/{self.location}/{name}"
        # Fallback to default behavior
        return super().url(name, parameters, expire)
