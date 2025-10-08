# login/views.py
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import base64
import hashlib
import hmac
from datetime import datetime, timedelta

# Use Django's secret key for signing
from django.conf import settings

class SimpleJWT:
    """A simple JWT implementation using Django's SECRET_KEY"""
    
    @staticmethod
    def encode(payload):
        """Encode a JWT token"""
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        
        # Encode header and payload
        header_encoded = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip('=')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')
        
        # Create signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        return f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    
    @staticmethod
    def decode(token):
        """Decode and verify a JWT token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
                
            header_encoded, payload_encoded, signature_encoded = parts
            
            # Add padding back if needed
            payload_encoded += '=' * (4 - len(payload_encoded) % 4)
            
            # Verify signature
            message = f"{header_encoded}.{payload_encoded.rstrip('=')}"
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            
            expected_signature_encoded = base64.urlsafe_b64encode(expected_signature).decode().rstrip('=')
            
            if not hmac.compare_digest(signature_encoded, expected_signature_encoded):
                return None
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_encoded)
            payload = json.loads(payload_json)
            
            # Check expiration
            if 'exp' in payload:
                if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                    return None
            
            return payload
            
        except Exception:
            return None

def generate_tokens(user):
    """Generate access and refresh tokens for a user"""
    # Access token (15 minutes expiry)
    access_token_payload = {
        'user_id': user.id,
        'email': user.email,
        'username': user.username,
        'is_superuser': user.is_superuser,
        'exp': (datetime.utcnow() + timedelta(minutes=15)).timestamp(),
        'iat': datetime.utcnow().timestamp()
    }
    access_token = SimpleJWT.encode(access_token_payload)

    # Refresh token (7 days expiry)
    refresh_token_payload = {
        'user_id': user.id,
        'exp': (datetime.utcnow() + timedelta(days=7)).timestamp(),
        'iat': datetime.utcnow().timestamp()
    }
    refresh_token = SimpleJWT.encode(refresh_token_payload)

    return access_token, refresh_token

@api_view(['POST'])
def login_view(request):
    try:
        data = json.loads(request.body)
        username_or_email = data.get('email')  # Can be username or email
        password = data.get('password')

        print(f"Login attempt for: {username_or_email}")

        # Try to find user by username or email
        try:
            # First try username
            user = User.objects.get(username=username_or_email)
            print(f"User found by username: {user.username}")
        except User.DoesNotExist:
            try:
                # Then try email
                user = User.objects.get(email=username_or_email)
                print(f"User found by email: {user.username}")
            except User.DoesNotExist:
                print("User not found")
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)

        # Check if user is superuser
        if not user.is_superuser:
            print("User is not a superuser")
            return Response({
                'error': 'Access denied. Superuser privileges required.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Simple password check
        if user.check_password(password):
            print("Password check successful")
            access_token, refresh_token = generate_tokens(user)
            
            return Response({
                'access': access_token,
                'refresh': refresh_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_superuser': user.is_superuser
                }
            }, status=status.HTTP_200_OK)
        else:
            print("Password check failed")
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        print(f"Login error: {str(e)}")
        return Response({
            'error': 'Something went wrong. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def refresh_token_view(request):
    try:
        data = json.loads(request.body)
        refresh_token = data.get('refresh')

        payload = SimpleJWT.decode(refresh_token)
        if not payload:
            return Response({
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user_id = payload.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            
            # Check if user is still a superuser
            if not user.is_superuser:
                return Response({
                    'error': 'Superuser privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
                
            access_token, new_refresh_token = generate_tokens(user)
            
            return Response({
                'access': access_token,
                'refresh': new_refresh_token
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({
            'error': 'Token refresh failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def protected_view(request):
    """Example protected view that requires JWT authentication"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return Response({
            'error': 'Authorization header missing or invalid'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header.split(' ')[1]
    
    payload = SimpleJWT.decode(token)
    if not payload:
        return Response({
            'error': 'Invalid or expired token'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user_id = payload.get('user_id')
    
    try:
        user = User.objects.get(id=user_id)
        
        # Check if user is superuser
        if not user.is_superuser:
            return Response({
                'error': 'Superuser privileges required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'message': f'Hello Superuser {user.username}! This is a protected endpoint.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_401_UNAUTHORIZED)

# Test view to check if API is working
@api_view(['GET'])
def test_view(request):
    return Response({
        'message': 'API is working!',
        'status': 'success',
        'endpoints': {
            'login': '/api/login/',
            'refresh': '/api/refresh/',
            'protected': '/api/protected/',
            'test': '/api/test/'
        },
        'note': 'Only superusers can login. Accepts username or email.'
    }, status=status.HTTP_200_OK)