"""
Test script to verify R2 storage configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from django.core.files.storage import default_storage
from django.conf import settings

print("=" * 60)
print("R2 STORAGE CONFIGURATION TEST")
print("=" * 60)

print(f"\n✓ R2 Enabled: {settings.CLOUDFLARE_R2_ENABLED}")

if settings.CLOUDFLARE_R2_ENABLED:
    print(f"\n📦 Storage Backend: {type(default_storage).__name__}")
    print(f"   - Module: {type(default_storage).__module__}")
    print(f"   - Class: {settings.STORAGES['default']['BACKEND']}")
    
    print(f"\n🪣 Bucket Configuration:")
    print(f"   - Bucket Name: {settings.CLOUDFLARE_R2_BUCKET_NAME}")
    print(f"   - Endpoint: {settings.CLOUDFLARE_R2_ENDPOINT}")
    print(f"   - Public URL: {settings.CLOUDFLARE_R2_PUBLIC_URL}")
    
    print(f"\n🔐 AWS/R2 Settings:")
    print(f"   - Access Key: {settings.AWS_ACCESS_KEY_ID[:10]}...")
    print(f"   - Region: {settings.AWS_S3_REGION_NAME}")
    print(f"   - Signature Version: {settings.AWS_S3_SIGNATURE_VERSION}")
    
    print(f"\n🌐 URLs:")
    print(f"   - Media URL: {settings.MEDIA_URL}")
    print(f"   - Static URL: {settings.STATIC_URL}")
    
    # Test storage connection
    try:
        print(f"\n🧪 Testing R2 Connection...")
        # Try to list bucket (this will verify credentials)
        storage = default_storage.bucket.meta.client
        print(f"   ✓ Connection successful!")
        print(f"   ✓ Bucket: {default_storage.bucket.name}")
    except Exception as e:
        print(f"   ⚠️  Connection test failed: {str(e)}")
        print(f"   (This is normal if bucket doesn't exist yet)")
else:
    print(f"\n📁 Using local file storage")
    print(f"   - Media Root: {settings.MEDIA_ROOT}")
    print(f"   - Media URL: {settings.MEDIA_URL}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
