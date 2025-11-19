from rest_framework import serializers
from .models import OfferLetter
from interview_management.models import Interview


class OfferLetterSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone_number', read_only=True)
    candidate_cv = serializers.FileField(source='candidate.cv_file',read_only=True)
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = OfferLetter
        fields = [
            'id', 'candidate', 'candidate_name', 'candidate_email', 'candidate_phone',
            'position', 'department', 'salary', 'joining_data', 'notice_period',
            'work_start_time', 'work_end_time',
            'subject', 'body', 'terms_condition', 'pdf_file',
            'candidate_cv',
            'candidate_status', 'rejection_status',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
    # Make candidate and candidate_cv read-only during updates since they shouldn't change
    read_only_fields = ['candidate', 'candidate_cv', 'created_at', 'updated_at', 'created_by', 'created_by_name']

    def validate_candidate(self, value):
        """Ensure candidate has selected status"""
        # IMPORTANT: If updating and candidate is the same, skip all validation
        if self.instance:
            # Compare UUID strings to handle both UUID objects and string comparisons
            current_candidate_id = str(self.instance.candidate.id)
            new_candidate_id = str(value.id) if hasattr(value, 'id') else str(value)
            
            if current_candidate_id == new_candidate_id:
                return value
            
        # Check interview status
        if hasattr(value, 'interview_status') and value.interview_status != 'selected':
            raise serializers.ValidationError("Offer letters can only be created for candidates with 'selected' status.")
        
        # Check if offer letter already exists for this candidate (excluding current instance during update)
        queryset = OfferLetter.objects.filter(candidate=value)
        if self.instance:
            # Exclude the current offer letter instance
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("An offer letter already exists for this candidate.")
        
        return value
    
   
    def validate_joining_data(self, value):
        """Ensure joining date is in the future"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Joining date must be in the future.")
        return value
    
    def update(self, instance, validated_data):
        """Custom update to handle OneToOne relationship properly"""
        # If candidate in validated_data is the same as current, remove it to avoid OneToOne error
        if 'candidate' in validated_data:
            if str(validated_data['candidate'].id) == str(instance.candidate.id):
                validated_data.pop('candidate')
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance




class OfferLetterCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating offer letters"""
    
    class Meta:
        model = OfferLetter
        fields = [
            'candidate', 'position', 'department', 'salary',
            'work_start_time', 'work_end_time', 'joining_data', 'notice_period',
            'subject', 'body', 'terms_condition'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

    def validate_candidate(self, value):
        """Ensure candidate has selected status and doesn't already have an offer"""
        # Check interview status
        if hasattr(value, 'interview_status') and value.interview_status != 'selected':
            raise serializers.ValidationError("Offer letters can only be created for candidates with 'selected' status.")

        # Check if offer letter already exists for this candidate
        if OfferLetter.objects.filter(candidate=value).exists():
            raise serializers.ValidationError("An offer letter already exists for this candidate.")

        return value



class SelectedCandidatesSerializer(serializers.ModelSerializer):
    """Serializer for listing candidates available for offer letters"""
    name = serializers.CharField(source='candidate.name', read_only=True)
    email = serializers.EmailField(source='candidate.email', read_only=True)
    phone_number = serializers.CharField(source='candidate.phone_number', read_only=True)
    job_title_name = serializers.CharField(source='candidate.job_title.title', read_only=True)
    candidate_id = serializers.UUIDField(source='candidate.id', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id', 'candidate_id', 'name', 'phone_number', 'job_title_name', 'status','email'
        ]
