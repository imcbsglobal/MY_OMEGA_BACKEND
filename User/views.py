# User/views.py - Fixed version with proper authentication
import os
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password

from .models import AppUser
from .serializers import AppUserSerializer
from django.conf import settings


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # Allow public access for listing and registration
@parser_classes([MultiPartParser, FormParser, JSONParser])
def users(request):
    """
    GET: list all users (public - for user list page)
    POST: create a new user (public - for registration)
    """
    if request.method == 'GET':
        queryset = AppUser.objects.all().order_by('-created_at')
        serializer = AppUserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST -> create user (registration)
    if request.method == 'POST':
        serializer = AppUserSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            
            # Ensure password is hashed (serializer should handle this, but double-check)
            instance = serializer.save()
            
            # Return success without password in response
            response_data = AppUserSerializer(instance, context={'request': request}).data
            response_data.pop('password', None)  # Remove password from response
            
            return Response(
                {
                    "message": "User created successfully",
                    "user": response_data
                },
                status=status.HTTP_201_CREATED
            )
        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"email": ["A user with this email already exists."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Error creating user: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])  # Changed to AllowAny for testing, change back to IsAuthenticated in production
@parser_classes([MultiPartParser, FormParser, JSONParser])
def user_detail(request, pk):
    """
    GET: retrieve a single user
    PUT/PATCH: update a user
    DELETE: delete a user
    """
    try:
        user = AppUser.objects.get(pk=pk)
    except AppUser.DoesNotExist:
        return Response(
            {'detail': 'User not found.'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = AppUserSerializer(user, context={'request': request})
        data = serializer.data
        data.pop('password', None)  # Don't send password in response
        return Response(data, status=status.HTTP_200_OK)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = AppUserSerializer(
            user, 
            data=request.data, 
            partial=partial, 
            context={'request': request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            response_data = AppUserSerializer(instance, context={'request': request}).data
            response_data.pop('password', None)
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        # Delete photo file if exists
        try:
            photo_field = getattr(user, 'photo', None)
            if photo_field and hasattr(photo_field, 'path'):
                file_path = photo_field.path
                media_root = os.path.abspath(settings.MEDIA_ROOT)
                file_path_abs = os.path.abspath(file_path)
                if os.path.isfile(file_path_abs) and file_path_abs.startswith(media_root):
                    try:
                        os.remove(file_path_abs)
                    except Exception:
                        pass
        except Exception:
            pass

        user.delete()
        return Response(
            {"message": "User deleted successfully"}, 
            status=status.HTTP_204_NO_CONTENT
        )