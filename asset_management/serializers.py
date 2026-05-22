from rest_framework import serializers

from employee_management.models import Employee

from .models import Asset


class AssetEmployeeSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['id', 'employee_name']

    def get_employee_name(self, obj):
        return obj.get_full_name()


class AssetListSerializer(serializers.ModelSerializer):
    employee_info = AssetEmployeeSerializer(source='employee', read_only=True)
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            'id',
            'asset_name',
            'asset_tag',
            'category',
            'serial_number',
            'employee',
            'employee_name',
            'employee_info',
            'description',
            'condition',
            'status',
            'assigned_date',
            'return_date',
            'created_at',
            'updated_at',
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else ''


class AssetDetailSerializer(serializers.ModelSerializer):
    employee_info = AssetEmployeeSerializer(source='employee', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            'id',
            'asset_name',
            'asset_tag',
            'category',
            'serial_number',
            'employee',
            'employee_name',
            'employee_info',
            'description',
            'condition',
            'status',
            'assigned_date',
            'return_date',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else ''

    def get_created_by_name(self, obj):
        if obj.created_by:
            if hasattr(obj.created_by, 'get_full_name'):
                return obj.created_by.get_full_name()
            return str(obj.created_by)
        return None


class AssetCreateUpdateSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.select_related('user').all())

    class Meta:
        model = Asset
        fields = [
            'asset_name',
            'asset_tag',
            'category',
            'serial_number',
            'employee',
            'description',
            'condition',
            'status',
            'assigned_date',
            'return_date',
        ]

    def validate_asset_tag(self, value):
        queryset = Asset.objects.filter(asset_tag=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('An asset with this tag already exists.')
        return value

    def validate(self, attrs):
        assigned_date = attrs.get('assigned_date', getattr(self.instance, 'assigned_date', None))
        return_date = attrs.get('return_date', getattr(self.instance, 'return_date', None))
        if assigned_date and return_date and return_date < assigned_date:
            raise serializers.ValidationError({'return_date': 'Return date cannot be earlier than assigned date.'})
        return attrs
