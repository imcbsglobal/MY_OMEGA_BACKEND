from rest_framework import serializers
from .models import WarehouseTask


class WarehouseTaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()
    completion_percentage = serializers.ReadOnlyField()

    class Meta:
        model = WarehouseTask
        fields = [
            'id',
            'task_title',
            'description',
            'assigned_by',
            'assigned_by_name',
            'assigned_to',
            'assigned_to_name',
            'assigned_date',
            'due_date',
            'total_work',
            'completed_work',
            'completion_percentage',
            'status',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['assigned_by', 'created_at', 'updated_at']

    def get_assigned_to_name(self, obj):
        user = obj.assigned_to
        return getattr(user, 'name', None) or getattr(user, 'email', str(user))

    def get_assigned_by_name(self, obj):
        user = obj.assigned_by
        return getattr(user, 'name', None) or getattr(user, 'email', str(user))


class WarehouseTaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseTask
        fields = [
            'task_title',
            'description',
            'assigned_to',
            'assigned_date',
            'due_date',
            'total_work',
        ]

    def validate_total_work(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total work must be greater than 0.")
        return value

    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)


class WarehouseTaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseTask
        fields = ['completed_work', 'status', 'remarks']

    def validate(self, data):
        instance = self.instance
        completed = data.get('completed_work', instance.completed_work if instance else 0)
        total = instance.total_work if instance else 0

        if completed > total:
            raise serializers.ValidationError(
                {'completed_work': f'Completed work ({completed}) cannot exceed total work ({total}).'}
            )
        return data
