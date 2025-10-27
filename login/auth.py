# login/auth.py - JWT Authentication Middleware
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from User.models import AppUser
import json
import base64
import hashlib
import hmac
from datetime import datetime
from django.conf import settings


class SimpleJWT:
    @staticmethod
    def _b64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode().rstrip('=')

    @staticmethod
    def _b64_decode(data: str) -> bytes:
        padding = '=' * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    @staticmethod
    def decode(token: str):
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header_encoded, payload_encoded, signature_encoded = parts
            message = f"{header_encoded}.{payload_encoded}"
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode(), 
                message.encode(), 
                hashlib.sha256
            ).digest()
            expected_sig_enc = SimpleJWT._b64_encode(expected_signature)
            if not hmac.compare_digest(signature_encoded, expected_sig_enc):
                return None
            payload_json = SimpleJWT._b64_decode(payload_encoded)
            payload = json.loads(payload_json)
            if 'exp' in payload and datetime.utcnow().timestamp() > float(payload['exp']):
                return None
            return payload
        except Exception:
            return None


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication for AppUser model.
    Add this to REST_FRAMEWORK settings:
    
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'login.auth.JWTAuthentication',
        ],
    }
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ', 1)[1]
        payload = SimpleJWT.decode(token)
        
        if not payload:
            raise AuthenticationFailed('Invalid or expired token')
        
        user_id = payload.get('user_id')
        if not user_id:
            raise AuthenticationFailed('Invalid token payload')
        
        try:
            user = AppUser.objects.get(pk=user_id)
        except AppUser.DoesNotExist:
            raise AuthenticationFailed('User not found')
        
        # Return (user, token_payload) tuple
        # DRF will set request.user = user
        return (user, payload)
    
    def authenticate_header(self, request):
        return 'Bearer'