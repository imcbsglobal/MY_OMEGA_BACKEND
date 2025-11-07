from rest_framework import serializers
from .models import UserCvData, JobTitle


class JobTitleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = JobTitle
        fields = ['id', 'title', 'created_at', 'updated_at']
        read_only_fields = [ 'created_at', 'updated_at']


class UserCvDataSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = UserCvData
        fields = [
            'uuid',
            'name',
            'gender',
            'dob',
            'job_title',
            'place',
            'district',
            'education',
            'experience',
            'email',
            'phone_number',
            'address',
            'cv_file',
            'cv_source',
            'interview_status',
            'remarks',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        """Automatically set created_by from request user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Custom update logic (optional)"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
