from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import LeaveMaster
from .serializers import LeaveMasterSerializer

class LeaveMasterViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Leave Master management
    
    Endpoints:
    - GET /api/leaves/ - List all leave types
    - POST /api/leaves/ - Create new leave type
    - GET /api/leaves/{id}/ - Get specific leave type
    - PUT /api/leaves/{id}/ - Update leave type
    - PATCH /api/leaves/{id}/ - Partial update leave type
    - DELETE /api/leaves/{id}/ - Delete leave type
    - GET /api/leaves/active/ - Get only active leave types
    - GET /api/leaves/categories/ - Get available categories
    """
    queryset = LeaveMaster.objects.all()
    permission_classes = [AllowAny]  # Change to [IsAuthenticated] if needed
    
    def get_serializer_class(self):
        # Use the same serializer for create/update since a separate
        # create serializer is not defined in `master.serializers`.
        if self.action in ['create', 'update', 'partial_update']:
            return LeaveMasterSerializer
        return LeaveMasterSerializer
    
    def list(self, request, *args, **kwargs):
        """Get all leave types"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
    
    def create(self, request, *args, **kwargs):
        """Create new leave type"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Leave type created successfully',
                'data': LeaveMasterSerializer(serializer.instance).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Get single leave type"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Update leave type"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Leave type updated successfully',
                'data': LeaveMasterSerializer(serializer.instance).data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete leave type"""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Leave type deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active leave types"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available leave categories"""
        categories = [
            {'value': choice[0], 'label': choice[1]}
            for choice in LeaveMaster.LEAVE_CATEGORIES
        ]
        payment_statuses = [
            {'value': choice[0], 'label': choice[1]}
            for choice in LeaveMaster.PAYMENT_STATUS
        ]
        return Response({
            'success': True,
            'data': {
                'categories': categories,
                'payment_statuses': payment_statuses
            }
        })