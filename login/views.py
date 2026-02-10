# login/views.py - Complete and Fixed
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

from User.models import AppUser
from User.serializers import AppUserSerializer
from user_controll.models import MenuItem, UserMenuAccess

logger = logging.getLogger(__name__)


# ------------------------
# JWT Helper
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
    """Generate access and refresh tokens for AppUser"""
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
# Menu Tree Builder
# ------------------------
def serialize_menu_node(node, allowed_ids=None):
    """Build hierarchical menu tree"""
    base = {
        "id": node.id,
        "key": node.key,
        "name": node.name,
        "path": node.path,
        "icon": node.icon,
        "order": node.order,
        "children": []
    }

    children = list(node.children.filter(is_active=True).order_by("order", "name"))
    
    if allowed_ids is None:
        # Admin: include all children
        base["children"] = [serialize_menu_node(c, None) for c in children]
        return base

    # Regular user: only include allowed children
    kept = []
    for c in children:
        child_serialized = serialize_menu_node(c, allowed_ids)
        if c.id in allowed_ids or child_serialized["children"]:
            kept.append(child_serialized)
    
    base["children"] = kept
    return base


def _allowed_menus_for(user):
    """
    Get menu tree based on user level
    - Super Admin/Admin: ALL menus
    - User: Only assigned menus
    """
    # Check user level (matches AppUser.Levels choices)
    is_admin = user.user_level in ("Super Admin", "Admin")
    
    if is_admin:
        # Admin gets full menu tree
        roots = MenuItem.objects.filter(
            is_active=True, 
            parent__isnull=True
        ).prefetch_related('children').order_by("order", "name")
        
        menu_tree = [serialize_menu_node(r, None) for r in roots]
        return is_admin, menu_tree
    
    else:
        # Regular users get only assigned menus
        allowed_ids = set(
            UserMenuAccess.objects
            .filter(user=user, menu_item__is_active=True)
            .values_list("menu_item_id", flat=True)
        )
        
        if not allowed_ids:
            return is_admin, []
        
        # Build filtered tree
        roots = MenuItem.objects.filter(
            is_active=True,
            parent__isnull=True
        ).prefetch_related('children').order_by("order", "name")
        
        menu_tree = []
        for r in roots:
            node = serialize_menu_node(r, allowed_ids)
            if r.id in allowed_ids or node["children"]:
                menu_tree.append(node)
        
        return is_admin, menu_tree


def _has_user_control_in_tree(menu_tree):
    """Check if user_control exists in menu tree"""
    for item in menu_tree:
        if item.get('key') == 'user_control':
            return True
        if item.get('children'):
            if _has_user_control_in_tree(item['children']):
                return True
    return False

# login/views.py - Updated login_view function
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login with menu-based access control.
    
    - Django superusers (is_superuser=True): Get ALL menus
    - ALL other users (including Admin/Super Admin): Get only assigned menus
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from User.models import AppUser
        
        # Get user
        try:
            user = AppUser.objects.get(email=email)
        except AppUser.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check password
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Account disabled'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Handle photo URL safely
        photo_url = None
        if user.photo:
            try:
                photo_url = request.build_absolute_uri(user.photo.url)
            except Exception as e:
                print(f"Warning: Could not get photo URL: {e}")
                photo_url = None
        
        # Determine access level
        is_django_superuser = user.is_superuser  # Django superuser
        is_app_admin = user.user_level in ('Super Admin', 'Admin')  # AppUser admin
        
        print(f"\n[LOGIN] User: {user.email}")
        print(f"[LOGIN] is_superuser (Django): {is_django_superuser}")
        print(f"[LOGIN] user_level (AppUser): {user.user_level}")
        print(f"[LOGIN] is_app_admin: {is_app_admin}")
        
        # Get menus based on user type
        allowed_menus = []
        
        if is_django_superuser:
            # Django superuser gets ALL menus
            print(f"[LOGIN] Django superuser - loading ALL menus")
            try:
                from user_controll.models import MenuItem
                all_menus = MenuItem.objects.filter(
                    is_active=True, 
                    parent__isnull=True
                ).order_by('order')
                
                allowed_menus = [
                    {
                        'id': m.id,
                        'key': m.key,
                        'name': m.name,
                        'path': m.path,
                        'icon': m.icon,
                        'order': m.order
                    }
                    for m in all_menus
                ]
                print(f"[LOGIN] Loaded {len(allowed_menus)} menus for Django superuser")
            except Exception as e:
                print(f"Warning: Could not load menus: {e}")
                allowed_menus = []
        else:
            # ALL other users (including Admin/Super Admin) get assigned menus only
            print(f"[LOGIN] Regular user/AppUser admin - loading ASSIGNED menus only")
            try:
                from user_controll.models import UserMenuAccess
                user_menus = UserMenuAccess.objects.filter(
                    user=user,
                    menu_item__is_active=True,
                    menu_item__parent__isnull=True
                ).select_related('menu_item').order_by('menu_item__order')
                
                allowed_menus = [
                    {
                        'id': a.menu_item.id,
                        'key': a.menu_item.key,
                        'name': a.menu_item.name,
                        'path': a.menu_item.path,
                        'icon': a.menu_item.icon,
                        'order': a.menu_item.order
                    }
                    for a in user_menus
                ]
                print(f"[LOGIN] Loaded {len(allowed_menus)} assigned menus")
            except Exception as e:
                print(f"Warning: Could not load menus: {e}")
                allowed_menus = []
        
        # Get Employee profile if exists
        employee_data = None
        try:
            if hasattr(user, 'employee_profile') and user.employee_profile:
                emp = user.employee_profile
                employee_data = {
                    'employee_id': emp.id,
                    'employee_code': emp.employee_id,
                    'full_name': emp.full_name or user.name,
                }
        except Exception as e:
            print(f"Warning: Could not load employee profile: {e}")
        
        # Build response
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'user_level': user.user_level,
                'job_role': user.job_role or '',
                'phone_number': user.phone_number or '',
                'photo': photo_url,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_django_superuser': is_django_superuser,
                'is_app_admin': is_app_admin,
            },
            'employee': employee_data,
            'user_level': user.user_level,
            'allowed_menus': allowed_menus,
            'is_django_superuser': is_django_superuser,
            'is_app_admin': is_app_admin,
            'can_access_control_panel': is_django_superuser or is_app_admin,
        })
        
    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print("LOGIN ERROR:")
        print("="*60)
        print(traceback.format_exc())
        print("="*60 + "\n")
        
        return Response(
            {'error': f'Login failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh_view(request):
    """Refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Token required'}, status=400)
        
        refresh = RefreshToken(refresh_token)
        return Response({'access': str(refresh.access_token)})
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=401)


@api_view(['GET'])
def protected_view(request):
    return Response({'detail': 'OK'})


@api_view(['POST'])
@permission_classes([AllowAny])
def token_login_view(request):
    return Response({'detail': 'Not implemented'}, status=501)