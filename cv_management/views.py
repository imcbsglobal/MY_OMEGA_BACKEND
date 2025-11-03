from django.shortcuts import render
from .models  import UserCvData,JobTitle
from .serializers import UserCvDataSerializer, JobTitleSerializer
from rest_framework import viewsets, permissions


class JobTitleViewSet(viewsets.ModelViewSet):
    quaryset = JobTitle.objects.all().order_by('-createdAt')
    serializer_class = JobTitleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class UserCvDataViewSet(viewsets.ModelViewSet):
    """CRUD API for Candidate CV data"""
    queryset = UserCvData.objects.all().order_by('-created_at')
    serializer_class = UserCvDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Automatically set created_by"""
        serializer.save(created_by=self.request.user)
