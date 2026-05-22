from django.db.models import Count, Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from employee_management.models import Employee

from .models import Asset
from .serializers import AssetCreateUpdateSerializer, AssetDetailSerializer, AssetEmployeeSerializer, AssetListSerializer


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related('employee', 'employee__user', 'created_by').all()
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AssetCreateUpdateSerializer
        if self.action == 'retrieve':
            return AssetDetailSerializer
        return AssetListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset_name__icontains=search)
                | Q(asset_tag__icontains=search)
                | Q(category__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(employee__employee_id__icontains=search)
                | Q(employee__full_name__icontains=search)
                | Q(employee__user__email__icontains=search)
            )

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)

        condition_filter = self.request.query_params.get('condition')
        if condition_filter:
            queryset = queryset.filter(condition__iexact=condition_filter)

        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category__icontains=category_filter)

        employee_filter = self.request.query_params.get('employee')
        if employee_filter:
            queryset = queryset.filter(employee_id=employee_filter)

        assigned_from = self.request.query_params.get('assigned_from')
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_from:
            queryset = queryset.filter(assigned_date__gte=assigned_from)
        if assigned_to:
            queryset = queryset.filter(assigned_date__lte=assigned_to)

        return queryset.order_by('-assigned_date', '-created_at', '-id')

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        counts = {row['status']: row['total'] for row in queryset.values('status').annotate(total=Count('id'))}
        return Response({
            'total_assets': queryset.count(),
            'available_assets': counts.get('available', 0),
            'assigned_assets': counts.get('assigned', 0),
            'returned_assets': counts.get('returned', 0),
            'maintenance_assets': counts.get('maintenance', 0),
            'retired_assets': counts.get('retired', 0),
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def employees_lookup(request):
    queryset = Employee.objects.select_related('user').filter(is_active=True).order_by('employee_id', 'full_name')
    serializer = AssetEmployeeSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)
