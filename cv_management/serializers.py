from rest_framework import serializers
from .models import UserCvData, JobTitle


class JobTitleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = JobTitle
        fields = ['id', 'title', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserCvDataSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    job_title = serializers.CharField()  # ✅ Change to CharField to accept string
    
    class Meta:
        model = UserCvData
        fields = [
            'id',
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
    
    def validate_job_title(self, value):
        """
        Accept both ID (integer) and title name (string)
        Convert to JobTitle object for database storage
        """
        # If it's an integer or digit string, treat as ID
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            try:
                return JobTitle.objects.get(pk=int(value))
            except JobTitle.DoesNotExist:
                raise serializers.ValidationError(f"Job title with ID '{value}' does not exist.")
        
        # If it's a string, treat as title name (case-insensitive)
        if isinstance(value, str):
            try:
                return JobTitle.objects.get(title__iexact=value.strip())
            except JobTitle.DoesNotExist:
                raise serializers.ValidationError(f"Job title '{value}' does not exist. Please use an existing job title.")
            except JobTitle.MultipleObjectsReturned:
                raise serializers.ValidationError(f"Multiple job titles found with name '{value}'. Please use ID instead.")
        
        raise serializers.ValidationError("Invalid job title format. Provide either an ID or title name.")
    
    def to_representation(self, instance):
        """Override to return job title name instead of ID"""
        representation = super().to_representation(instance)
        # Replace job_title ID with title name
        if instance.job_title:
            representation['job_title'] = instance.job_title.title
        return representation

    def create(self, validated_data):
        """Automatically set created_by from request user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Custom update logic"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
