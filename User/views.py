# User/views.py - UPDATED VERSION (adds safe delete authorization + self-delete guard)
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from .models import AppUser
from .serializers import (
    AppUserSerializer, 
    AppUserCreateSerializer, 
    AppUserUpdateSerializer,
    PasswordChangeSerializer,
    UserBriefSerializer
)


class AppUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AppUser instances
    Provides CRUD operations for users/employees
    """
    queryset = AppUser.objects.all().order_by('-date_joined')
    serializer_class = AppUserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action"""
        if self.action == 'create':
            return AppUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppUserUpdateSerializer
        elif self.action == 'brief_list':
            return UserBriefSerializer
        return AppUserSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters
        Supports search by name, email, job_title, etc.
        """
        queryset = AppUser.objects.all().order_by('-date_joined')
        
        # Search parameter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(job_title__icontains=search) |
                Q(job_role__icontains=search) |
                Q(personal_phone__icontains=search)
            )
        
        # Filter by user_level
        user_level = self.request.query_params.get('user_level', None)
        if user_level:
            queryset = queryset.filter(user_level=user_level)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by organization
        organization = self.request.query_params.get('organization', None)
        if organization:
            queryset = queryset.filter(organization__icontains=organization)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new user/employee"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return full user details
        response_serializer = AppUserSerializer(user, context={'request': request})
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update user/employee"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return full user details
        response_serializer = AppUserSerializer(user, context={'request': request})
        return Response(response_serializer.data)

    # --- NEW: harden delete with role checks and self-delete guard ---
    def destroy(self, request, *args, **kwargs):
        """
        Only allow 'Super Admin' or Django superuser to delete users.
        Prevent a user from deleting themselves.
        """
        target = self.get_object()
        actor = request.user

        # Block self-delete to avoid accidental lockouts
        if target.id == actor.id:
            return Response(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only Super Admins or Django superusers can delete
        is_super_admin = getattr(actor, "user_level", "") == "Super Admin"
        if not (actor.is_superuser or is_super_admin):
            return Response(
                {"error": "You are not authorized to delete users."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Optional: prevent deleting another Super Admin unless Django superuser
        if getattr(target, "user_level", "") == "Super Admin" and not actor.is_superuser:
            return Response(
                {"error": "Only Django superusers can delete Super Admin accounts."},
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(target)
        return Response(status=status.HTTP_204_NO_CONTENT)
    # ----------------------------------------------------------------

    @action(detail=False, methods=['get'])
    def brief_list(self, request):
        """
        Get brief list of users (for dropdowns, etc.)
        URL: /api/users/brief_list/
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = UserBriefSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """
        Change password for a specific user
        URL: /api/users/{id}/change_password/
        """
        user = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current logged-in user details
        URL: /api/users/me/
        """
        serializer = AppUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        """
        Update current logged-in user profile
        URL: /api/users/update_me/
        """
        serializer = AppUserUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        response_serializer = AppUserSerializer(user, context={'request': request})
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get user statistics
        URL: /api/users/stats/
        """
        total_users = AppUser.objects.count()
        active_users = AppUser.objects.filter(is_active=True).count()
        inactive_users = AppUser.objects.filter(is_active=False).count()
        
        user_levels = {}
        for level, _ in AppUser.USER_LEVEL_CHOICES:
            user_levels[level] = AppUser.objects.filter(user_level=level).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'user_levels': user_levels,
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint
    POST /api/login/
    Body: {"email": "user@example.com", "password": "password123"}
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from user_controll.models import UserMenuAccess, MenuItem
    
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = AppUser.objects.get(email=email.lower())
    except AppUser.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.check_password(password):
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Account is disabled'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    refresh['user_level'] = user.user_level
    refresh['email'] = user.email
    refresh['name'] = user.name
    
    is_admin = user.user_level in ('Super Admin', 'Admin') or user.is_staff or user.is_superuser
    
    # Get photo URL
    photo_url = None
    if user.photo:
        photo_url = request.build_absolute_uri(user.photo.url)
    
    # Get menus
    try:
        if is_admin:
            all_menus = MenuItem.objects.filter(is_active=True, parent__isnull=True).order_by('order')
            allowed_menus = [
                {'id': m.id, 'key': m.key, 'name': m.name, 'path': m.path, 'icon': m.icon, 'order': m.order}
                for m in all_menus
            ]
        else:
            user_menus = UserMenuAccess.objects.filter(
                user_id=user.id,
                menu_item__is_active=True,
                menu_item__parent__isnull=True
            ).select_related('menu_item').order_by('menu_item__order')
            
            allowed_menus = [
                {'id': a.menu_item.id, 'key': a.menu_item.key, 'name': a.menu_item.name,
                 'path': a.menu_item.path, 'icon': a.menu_item.icon, 'order': a.menu_item.order}
                for a in user_menus
            ]
    except:
        # If user_controll app doesn't exist, return empty menus
        allowed_menus = []
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'user_level': user.user_level,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_admin': is_admin,
            'job_title': user.job_title,
            'job_role': user.job_role,
            'phone_number': user.phone_number or user.personal_phone,
            'personal_phone': user.personal_phone,
            'photo_url': photo_url,
        },
        'allowed_menus': allowed_menus,
        'is_admin': is_admin
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint (optional - for token blacklisting)
    POST /api/logout/
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Successfully logged out.'
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({
            'error': 'Invalid token or token already blacklisted.'
        }, status=status.HTTP_400_BAD_REQUEST)
