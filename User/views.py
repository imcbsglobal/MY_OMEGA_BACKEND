from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError

from .models import AppUser
from .serializers import AppUserSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def users(request):
    if request.method == 'GET':
        queryset = AppUser.objects.all().order_by('-created_at')
        serializer = AppUserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = AppUserSerializer(data=request.data, context={'request': request})
    try:
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
    except ValidationError as ve:
        return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        return Response({"user_id": ["This user_id already exists."]}, status=status.HTTP_400_BAD_REQUEST)

    return Response(AppUserSerializer(instance, context={'request': request}).data,
                    status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def user_detail(request, pk):
    instance = get_object_or_404(AppUser, pk=pk)

    if request.method == 'GET':
        return Response(AppUserSerializer(instance, context={'request': request}).data)

    if request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = AppUserSerializer(instance, data=request.data,
                                       partial=partial, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            updated = serializer.save()
        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({"user_id": ["This user_id already exists."]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AppUserSerializer(updated, context={'request': request}).data)

    if request.method == 'DELETE':
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
