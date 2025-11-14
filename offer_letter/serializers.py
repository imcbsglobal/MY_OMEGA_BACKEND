from rest_framework import serializers
from .models import OfferLetter
from interview_management.models import Interview


class OfferLetterSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = OfferLetter
        fields = [
            'id', 'candidate', 'candidate_name', 'candidate_email', 'candidate_phone',
            'position', 'department', 'salary', 'currency', 'joining_date', 'probation_period',
            'subject', 'body', 'terms_conditions', 'pdf_file',
            'status', 'sent_at', 'accepted_at', 'rejected_at', 'rejection_reason',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'created_by_name']
    
    def validate_candidate(self, value):
        """Ensure candidate has selected status"""
        if value.interview_status != 'selected':
            raise serializers.ValidationError("Offer letters can only be created for candidates with 'selected' status.")
        return value
    
    def validate_joining_date(self, value):
        """Ensure joining date is in the future"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Joining date must be in the future.")
        return value


class OfferLetterCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating offer letters"""
    
    class Meta:
        model = OfferLetter
        fields = [
            'candidate', 'position', 'department', 'salary', 'currency', 
            'joining_date', 'probation_period', 'subject', 'body', 'terms_conditions'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class SelectedCandidatesSerializer(serializers.ModelSerializer):
    """Serializer for listing candidates available for offer letters"""
    name = serializers.CharField(source='candidate.name', read_only=True)
    # email = serializers.EmailField(source='candidate.email', read_only=True)
    phone_number = serializers.CharField(source='candidate.phone_number', read_only=True)
    # job_title = serializers.PrimaryKeyRelatedField(source='candidate.job_title', read_only=True)
    job_title_name = serializers.CharField(source='candidate.job_title.title', read_only=True)
    # experience = serializers.CharField(source='candidate.experience', read_only=True)
    # education = serializers.CharField(source='candidate.education', read_only=True)
    # place = serializers.CharField(source='candidate.place', read_only=True)
    # district = serializers.CharField(source='candidate.district', read_only=True)
    candidate_id = serializers.UUIDField(source='candidate.id', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id', 'candidate_id', 'name', 'phone_number', 'job_title_name', 'status'
        ]
