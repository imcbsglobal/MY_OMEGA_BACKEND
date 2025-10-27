# login/views.py
import json
import base64
import hashlib
import hmac
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

# Models/serializers live in the User app
from User.models import AppUser
from User.serializers import AppUserSerializer

logger = logging.getLogger(__name__)


# ------------------------
# Minimal JWT helper (HS256)
# ------------------------
class SimpleJWT:
    @staticmethod
    def _b64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode().rstrip('=')

    @staticmethod
    def _b64_decode(data: str) -> bytes:
        padding = '=' * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    @staticmethod
    def encode(payload: dict) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_encoded = SimpleJWT._b64_encode(json.dumps(header, separators=(',', ':')).encode())
        payload_encoded = SimpleJWT._b64_encode(json.dumps(payload, separators=(',', ':')).encode())
        message = f"{header_encoded}.{payload_encoded}"
        secret = settings.SECRET_KEY.encode()
        signature = hmac.new(secret, message.encode(), hashlib.sha256).digest()
        signature_encoded = SimpleJWT._b64_encode(signature)
        return f"{header_encoded}.{payload_encoded}.{signature_encoded}"

    @staticmethod
    def decode(token: str):
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header_enc, payload_enc, sig_enc = parts
            message = f"{header_enc}.{payload_enc}"
            expected_sig = hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
            expected_sig_enc = SimpleJWT._b64_encode(expected_sig)
            if not hmac.compare_digest(sig_enc, expected_sig_enc):
                return None
            payload_json = SimpleJWT._b64_decode(payload_enc)
            payload = json.loads(payload_json)
            exp = payload.get('exp')
            if exp and datetime.utcnow().timestamp() > float(exp):
                return None
            return payload
        except Exception as e:
            logger.exception("SimpleJWT.decode error: %s", e)
            return None


def generate_tokens(user):
    now_ts = datetime.utcnow().timestamp()
    access_payload = {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "user_level": user.user_level,
        "iat": now_ts,
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
    }
    refresh_payload = {
        "user_id": user.id,
        "iat": now_ts,
        "exp": (datetime.utcnow() + timedelta(days=7)).timestamp(),
    }
    access = SimpleJWT.encode(access_payload)
    refresh = SimpleJWT.encode(refresh_payload)
    return access, refresh


# ------------------------
# Auth endpoints
# ------------------------
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST { "email": "<email>", "password": "<password>" } -> {access, refresh, user}
    """
    email = (request.data.get('email') or request.data.get('username') or '').strip()
    password = request.data.get('password')

    if not email:
        return Response({"detail": "email is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not password:
        return Response({"detail": "password is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = AppUser.objects.get(email__iexact=email)
    except AppUser.DoesNotExist:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        logger.exception("DB error fetching user %s: %s", email, e)
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        valid = check_password(password, user.password)
        # One-time plaintext fallback for legacy rows
        if not valid:
            looks_hashed = any(user.password.startswith(p) for p in ("pbkdf2_", "argon2", "bcrypt", "sha1$"))
            if not looks_hashed and password == user.password:
                user.password = make_password(password)
                user.save(update_fields=["password"])
                valid = True
    except Exception as e:
        logger.exception("Password check error for %s: %s", email, e)
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not valid:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    access, refresh = generate_tokens(user)
    user_data = AppUserSerializer(user, context={'request': request}).data
    user_data.pop('password', None)
    return Response({"access": access, "refresh": refresh, "user": user_data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """POST { "refresh": "<token>" } -> {access, refresh}"""
    refresh_token = request.data.get('refresh') or request.data.get('refreshToken')
    if not refresh_token:
        return Response({"detail": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

    payload = SimpleJWT.decode(refresh_token)
    if not payload:
        return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get('user_id')
    if not user_id:
        return Response({"detail": "Invalid token payload"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return Response({"detail": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)

    access, refresh = generate_tokens(user)
    return Response({"access": access, "refresh": refresh}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def protected_view(request):
    """Header Authorization: Bearer <access>"""
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return Response({"detail": "Authorization header missing or malformed"}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth.split(' ', 1)[1]
    payload = SimpleJWT.decode(token)
    if not payload:
        return Response({"detail": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({"detail": "ok", "payload": payload}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def token_login_view(request):
    """
    POST { "access":"<token>" } OR { "refresh":"<token>" }
    - If refresh: mint fresh access+refresh and return user
    - If valid access: return same access + fresh refresh and user
    """
    access_token = request.data.get('access')
    refresh_token = request.data.get('refresh')

    if not access_token and not refresh_token:
        return Response({"detail": "Provide 'access' or 'refresh' token."}, status=status.HTTP_400_BAD_REQUEST)

    token_to_decode = refresh_token or access_token
    payload = SimpleJWT.decode(token_to_decode)
    if not payload:
        return Response({"detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get('user_id')
    if not user_id:
        return Response({"detail": "Invalid token payload (no user_id)."}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED)

    if refresh_token:
        new_access, new_refresh = generate_tokens(user)
        user_data = AppUserSerializer(user, context={'request': request}).data
        user_data.pop('password', None)
        return Response({"access": new_access, "refresh": new_refresh, "user": user_data}, status=status.HTTP_200_OK)

    # access token path (valid)
    _, fresh_refresh = generate_tokens(user)
    user_data = AppUserSerializer(user, context={'request': request}).data
    user_data.pop('password', None)
    return Response({"access": access_token, "refresh": fresh_refresh, "user": user_data}, status=status.HTTP_200_OK)
