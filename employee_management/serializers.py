# employee_management/serializers.py - COMPLETE FIX
from rest_framework import serializers
from django.apps import apps
from .models import Employee, EmployeeDocument

# Try to get AppUser model
UserModel = None
try:
    from User.models import AppUser as UserModel
except Exception:
    try:
        UserModel = apps.get_model('User', 'AppUser')
    except Exception:
        UserModel = None


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'email', 'name'] if UserModel and hasattr(UserModel, 'name') else ['id', 'email']


class JobInfoSerializer(serializers.ModelSerializer):
    reporting_manager_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'user', 'user_name', 'user_email',
            'employment_status', 'employment_type', 'department', 'designation',
            'reporting_manager', 'reporting_manager_name', 'date_of_joining',
            'date_of_leaving', 'probation_end_date', 'confirmation_date',
            'basic_salary', 'allowances', 'gross_salary', 'location', 
            'work_location', 'duty_time'
        ]

    def get_reporting_manager_name(self, obj):
        mgr = getattr(obj, 'reporting_manager', None)
        if not mgr:
            return ''
        return getattr(mgr, 'full_name', None) or getattr(mgr, 'employee_id', str(mgr.pk))

    def get_user_email(self, obj):
        u = getattr(obj, 'user', None)
        return u.email if u else ''

    def get_user_name(self, obj):
        u = getattr(obj, 'user', None)
        if not u:
            return ''
        if hasattr(u, 'get_full_name'):
            try:
                return u.get_full_name()
            except:
                pass

        for attr in ('full_name', 'name', 'username', 'first_name'):
            if hasattr(u, attr):
                value = getattr(u, attr)
                if callable(value):
                    try: value = value()
                    except: value = ''
                if value:
                    return value

        return str(u)


class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relation', 'phone_number'
        ]


class PersonalInfoSerializer(serializers.ModelSerializer):
    """NEW: Serializer for personal information fields"""
    class Meta:
        model = Employee
        fields = [
            'blood_group', 'marital_status', 'notes'
        ]


class BankInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'salary_account_number', 'salary_bank_name', 'salary_ifsc_code',
            'salary_branch', 'account_holder_name', 'pf_number', 'esi_number',
            'pan_number', 'aadhar_number'
        ]


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'document_type', 'title', 'document_file', 
            'issue_date', 'expiry_date', 'notes'
        ]


class EmployeeListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    job_info = JobInfoSerializer(source='*', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'user_email',
            'avatar_url', 'profile_picture',
            'designation', 'department', 'employment_status',
            'employment_type', 'location', 'is_active', 'created_at',
            'job_info', 'phone_number'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_user_email(self, obj):
        return obj.user.email if obj.user else ''

    def get_avatar_url(self, obj):
        request = self.context.get('request')

        # Employee Avatar
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url

        # User Photo
        if obj.user and hasattr(obj.user, 'photo') and obj.user.photo:
            return request.build_absolute_uri(obj.user.photo.url) if request else obj.user.photo.url

        return None

    def get_profile_picture(self, obj):
        return self.get_avatar_url(obj)


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """COMPLETE DETAIL SERIALIZER - ALL FIELDS"""
    job_info = JobInfoSerializer(source='*', read_only=True)
    contact_info = ContactInfoSerializer(source='*', read_only=True)
    personal_info = PersonalInfoSerializer(source='*', read_only=True)
    bank_info = BankInfoSerializer(source='*', read_only=True)
    documents = EmployeeDocumentSerializer(source='additional_documents', many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            # Basic Info
            'id', 'employee_id', 'full_name', 'user_email', 'avatar_url',
            
            # Nested Serializers
            'job_info', 'contact_info', 'personal_info', 'bank_info', 'documents',
            
            # Direct Fields (for backwards compatibility and easy access)
            'designation', 'department', 'employment_status', 
            'employment_type', 'location', 'work_location',
            'phone_number',
            
            # Personal fields that were missing
            'blood_group', 'marital_status', 'notes',
            
            # Status
            'is_active', 'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_user_email(self, obj):
        return obj.user.email if obj.user else ''

    def get_avatar_url(self, obj):
        request = self.context.get('request')

        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url

        if obj.user and hasattr(obj.user, 'photo') and obj.user.photo:
            return request.build_absolute_uri(obj.user.photo.url) if request else obj.user.photo.url

        return None


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """COMPLETE CREATE/UPDATE SERIALIZER"""
    class Meta:
        model = Employee
        fields = [
            # User Link
            'user', 'employee_id', 'phone_number',
            
            # Job Information
            'employment_status', 'employment_type',
            'department', 'designation', 'reporting_manager',
            'date_of_joining', 'date_of_leaving', 'probation_end_date',
            'confirmation_date', 'basic_salary', 'allowances', 'gross_salary',
            'location', 'work_location', 'duty_time',
            
            # Government IDs
            'pf_number', 'esi_number', 'pan_number', 'aadhar_number',
            
            # Bank Details
            'account_holder_name', 'salary_account_number', 'salary_bank_name',
            'salary_ifsc_code', 'salary_branch',
            
            # Documents
            'pan_card_attachment', 'offer_letter', 'joining_letter', 'id_card_attachment',
            
            # Emergency Contact
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            
            # Personal Information
            'blood_group', 'marital_status', 'notes',
            
            # Avatar
            'avatar',
            
            # Status
            'is_active'
        ]

    def validate_user(self, value):
        if self.instance is None:
            if Employee.objects.filter(user=value).exists():
                raise serializers.ValidationError("This user already has an employee record.")
        return value

    def validate_employee_id(self, value):
        if value:
            qs = Employee.objects.filter(employee_id=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("An employee with this ID already exists.")
        return value