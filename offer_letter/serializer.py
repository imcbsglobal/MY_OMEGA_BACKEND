from rest_framework import serializers
from .models import OfferLetter
from cv_management.models import UserCvData


class OfferLetterSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta :
        model = OfferLetter
        fields = [
            'id', 'candidate', 'candidate_name', 'candidate_email', 'candidate_phone',
            'position', 'department', 'salary', 'currency', 'joining_date', 'probation_period',
            'subject', 'body', 'terms_conditions', 'pdf_file',
            'status', 'sent_at', 'accepted_at', 'rejected_at', 'rejection_reason',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'created_by_name']
    def validate_cadidate(self,value):
        if value.interview_status != 'selected':
            raise serializers.ValidationError("Offer letters can only be created for candidates with 'selected' status.")
        return value
    
    # def validate_joining_date(self, value):
    #     from django.utils import timezone
    #     if value < timezone.now().date():
    #         raise serializers.ValidationError("Joining date must be in the future.")
    #     return value
    

class OfferLetterCreateSerializers(serializers.ModelSerializer):
    class Meta :
        model = OfferLetter
        fields = [
            'candidate', 'position', 'department', 'salary', 'currency', 
            'joining_date', 'probation_period', 'subject', 'body', 'terms_conditions'
        ]
    
    def create(self,validated_data):
        request = self.context.get('request')
        if request and hasattr(request,'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)
    
class SelectedCandidatesSerializer(serializers.ModelSerializer):
    job_title_name = serializers.CharField(source='job_title.title', read_only=True)
    
    class Meta:
        model = UserCvData
        fields = [
            'id', 'name', 'email', 'phone_number', 'job_title', 'job_title_name',
            'experience', 'education', 'place', 'district'
        ]
        