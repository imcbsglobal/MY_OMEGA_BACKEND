from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from .serializers import SuperuserIDLoginSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def superuser_id_login(request):
    serializer = SuperuserIDLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data['user']
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    # Keep identical behavior to BaseTokenRefreshView
    from rest_framework_simplejwt.serializers import TokenRefreshSerializer
    serializer = TokenRefreshSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    u = request.user
    return Response({
        "id": u.id, "username": u.username, "email": u.email, "is_superuser": u.is_superuser
    })
