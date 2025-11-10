from rest_framework import serializers
from .models import Interview, InterviewEvaluation
from cv_management.models import UserCvData
from User.models import AppUser


# For dropdown to select one user to interview
class UserCvDropSerializer(serializers.ModelSerializer):
    """Lightweight serializer for CV dropdown selection"""
    job_title_name = serializers.CharField(source='job_title.title', read_only=True)
    
    class Meta:
        model = UserCvData
        fields = [
            'id',
            'name',
            'job_title',
            'job_title_name',
            'place',
            'email',
            'phone_number',
            'interview_status'
        ]


# Serializer to add selected user into interview table
class StartInterviewSerializer(serializers.Serializer):
    """Serializer for starting an interview - changes CV status to ongoing"""
    candidate_id = serializers.UUIDField(required=True)
    scheduled_at = serializers.DateTimeField(required=True)
    interviewer_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_candidate_id(self, value):
        """Validate that the candidate exists and is available for interview"""
        try:
            candidate = UserCvData.objects.get(id=value)
            
            # Check if already in ongoing, selected, or rejected status
            if candidate.interview_status == 'ongoing':
                raise serializers.ValidationError(
                    f"Interview for {candidate.name} is already in progress"
                )
            
            if candidate.interview_status in ['selected', 'rejected']:
                raise serializers.ValidationError(
                    f"Candidate status is '{candidate.interview_status}'. Cannot start new interview."
                )
            
            return value
        except UserCvData.DoesNotExist:
            raise serializers.ValidationError("Candidate with this ID does not exist")
    
    def validate_interviewer_id(self, value):
        """Validate that the interviewer exists"""
        if value is not None:
            try:
                AppUser.objects.get(id=value)
            except AppUser.DoesNotExist:
                raise serializers.ValidationError("Interviewer with this ID does not exist")
        return value


# For showing all interview selected users CVs that are available in interview table
class InterviewTableSerializer(serializers.ModelSerializer):
    """Serializer for listing interviews with candidate details"""
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone_number', read_only=True)
    job_title = serializers.CharField(source='candidate.job_title.title', read_only=True)
    place = serializers.CharField(source='candidate.place', read_only=True)
    district = serializers.CharField(source='candidate.district', read_only=True)
    interviewer_name = serializers.SerializerMethodField()
    has_evaluation = serializers.SerializerMethodField()
    cv_status = serializers.CharField(source='candidate.interview_status', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id',
            'candidate_name',
            'candidate_email',
            'candidate_phone',
            'job_title',
            'place',
            'district',
            'interviewer_name',
            'scheduled_at',
            'status',
            'cv_status',
            'has_evaluation',
            'created_at',
            'updated_at'
        ]
    
    def get_interviewer_name(self, obj):
        """Get full name of interviewer"""
        if obj.interviewer:
            return f"{obj.interviewer.first_name} {obj.interviewer.last_name}".strip() or obj.interviewer.email
        return None
    
    def get_has_evaluation(self, obj):
        """Check if interview has evaluation"""
        return hasattr(obj, 'evaluation')


# For getting ongoing interviews only
class OngoingInterviewSerializer(serializers.ModelSerializer):
    """Serializer specifically for ongoing interviews"""
    candidate = UserCvDropSerializer(read_only=True)
    interviewer_name = serializers.SerializerMethodField()
    evaluation_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Interview
        fields = [
            'id',
            'candidate',
            'interviewer_name',
            'scheduled_at',
            'status',
            'evaluation_completed',
            'created_at',
            'updated_at'
        ]
    
    def get_interviewer_name(self, obj):
        if obj.interviewer:
            return f"{obj.interviewer.first_name} {obj.interviewer.last_name}".strip() or obj.interviewer.email
        return None
    
    def get_evaluation_completed(self, obj):
        """Check if evaluation has meaningful data"""
        if hasattr(obj, 'evaluation'):
            eval_obj = obj.evaluation
            # Check if at least one rating field has a non-zero value
            return any([
                eval_obj.appearance > 0,
                eval_obj.knowledge > 0,
                eval_obj.confidence > 0,
                eval_obj.attitude > 0,
                eval_obj.communication > 0
            ])
        return False


# Interview Evaluation Serializer
class InterviewEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for interview evaluation with all rating fields"""
    average_rating = serializers.ReadOnlyField()
    interview_id = serializers.UUIDField(source='interview.id', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate.name', read_only=True)
    
    class Meta:
        model = InterviewEvaluation
        fields = [
            'interview_id',
            'candidate_name',
            'appearance',
            'knowledge',
            'confidence',
            'attitude',
            'communication',
            'languages',
            'expected_salary',
            'experience',
            'remark',
            'voice_note',
            'average_rating',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'average_rating']
    
    def validate(self, data):
        """Validate rating fields are within range"""
        rating_fields = ['appearance', 'knowledge', 'confidence', 'attitude', 'communication']
        for field in rating_fields:
            if field in data:
                value = data[field]
                if value is not None and (value < 0 or value > 10):
                    raise serializers.ValidationError({
                        field: f"Rating must be between 0 and 10"
                    })
        return data


# Status Update Serializer
class InterviewStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating interview status (selected/rejected/pending)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    ]
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=True)
    remark = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_status(self, value):
        """Ensure status is one of the allowed values"""
        if value not in ['pending', 'selected', 'rejected']:
            raise serializers.ValidationError(
                "Status must be one of: pending, selected, rejected"
            )
        return value


# Full Interview Detail Serializer
class InterviewDetailSerializer(serializers.ModelSerializer):
    """Complete interview details with all nested data"""
    candidate = UserCvDropSerializer(read_only=True)
    interviewer = serializers.SerializerMethodField()
    evaluation = InterviewEvaluationSerializer(read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id',
            'candidate',
            'interviewer',
            'scheduled_at',
            'status',
            'evaluation',
            'created_at',
            'updated_at'
        ]
    
    def get_interviewer(self, obj):
        """Get interviewer details"""
        if obj.interviewer:
            return {
                'id': obj.interviewer.id,
                'email': obj.interviewer.email,
                'first_name': obj.interviewer.first_name,
                'last_name': obj.interviewer.last_name,
                'job_role': obj.interviewer.job_role
            }
        return None


        
