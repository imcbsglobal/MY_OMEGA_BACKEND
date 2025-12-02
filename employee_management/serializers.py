# employee_management/serializers.py - FIXED
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
    """Job information nested serializer"""
    reporting_manager_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'user', 'user_name', 'user_email',  # <-- user_name now included
            'employment_status', 'employment_type', 'department', 'designation',
            'reporting_manager', 'reporting_manager_name', 'date_of_joining',
            'date_of_leaving', 'probation_end_date', 'confirmation_date',
            'basic_salary', 'allowances', 'gross_salary', 'location', 'work_location', 
            'duty_time'
        ]

    def get_reporting_manager_name(self, obj):
        mgr = getattr(obj, 'reporting_manager', None)
        if not mgr:
            return ''
        return getattr(mgr, 'full_name', None) or getattr(mgr, 'employee_id', str(mgr.pk))

    def get_user_email(self, obj):
        u = getattr(obj, 'user', None)
        return getattr(u, 'email', '') if u else ''

    def get_user_name(self, obj):
        u = getattr(obj, 'user', None)
        if not u:
            return ''
        if hasattr(u, 'get_full_name'):
            try:
                return u.get_full_name()
            except Exception:
                pass
        for attr in ('full_name', 'name', 'username', 'first_name'):
            if hasattr(u, attr):
                val = getattr(u, attr)
                if callable(val):
                    try:
                        val = val()
                    except Exception:
                        val = ''
                if val:
                    return val
        return str(u)


class ContactInfoSerializer(serializers.ModelSerializer):
    """Contact information nested serializer"""
    class Meta:
        model = Employee
        fields = [
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation'
        ]


class BankInfoSerializer(serializers.ModelSerializer):
    """Bank information nested serializer"""
    class Meta:
        model = Employee
        fields = [
            'salary_account_number', 'salary_bank_name', 'salary_ifsc_code', 
            'salary_branch', 'account_holder_name'
        ]


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    """Serializer for employee documents"""
    class Meta:
        model = EmployeeDocument
        fields = ['id', 'document_type', 'title', 'document_file', 'issue_date', 
                  'expiry_date', 'notes']


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for employee list view"""
    full_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    job_info = JobInfoSerializer(source='*', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'user_email', 'avatar_url',
            'designation', 'department', 'employment_status', 'employment_type',
            'location', 'is_active', 'created_at', 'job_info'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return ''

    def get_avatar_url(self, obj):
        if hasattr(obj, 'avatar') and obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        
        user = getattr(obj, 'user', None)
        if user and hasattr(user, 'photo') and user.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.photo.url)
            return user.photo.url
        return None


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Complete serializer for employee detail view"""
    job_info = JobInfoSerializer(source='*', read_only=True)
    contact_info = ContactInfoSerializer(source='*', read_only=True)
    bank_info = BankInfoSerializer(source='*', read_only=True)
    documents = EmployeeDocumentSerializer(source='additional_documents', many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'avatar_url',
            'job_info', 'contact_info', 'bank_info', 'documents',
            'designation', 'department', 'employment_status', 'employment_type',
            'location', 'work_location', 'blood_group', 'marital_status', 'notes',
            'is_active', 'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_avatar_url(self, obj):
        if hasattr(obj, 'avatar') and obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        
        user = getattr(obj, 'user', None)
        if user and hasattr(user, 'photo') and user.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.photo.url)
            return user.photo.url
        return None


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating employees"""
    
    class Meta:
        model = Employee
        fields = [
            'user', 'employee_id', 'phone_number',  # <-- phone_number added
            'employment_status', 'employment_type',
            'department', 'designation', 'reporting_manager',
            'date_of_joining', 'date_of_leaving', 'probation_end_date', 
            'confirmation_date', 'basic_salary', 'allowances', 'gross_salary',
            'pf_number', 'esi_number', 'pan_number', 'aadhar_number',
            'location', 'work_location', 'duty_time',
            'account_holder_name', 'salary_account_number', 'salary_bank_name',
            'salary_ifsc_code', 'salary_branch',
            'pan_card_attachment', 'offer_letter', 'joining_letter', 'id_card_attachment',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'blood_group', 'marital_status', 'notes', 'is_active'
        ]

    def validate_user(self, value):
        """Ensure user doesn't already have an employee record"""
        if self.instance is None:  # Only for creation
            if Employee.objects.filter(user=value).exists():
                raise serializers.ValidationError(
                    "This user already has an employee record."
                )
        return value

    def validate_employee_id(self, value):
        """Ensure employee ID is unique"""
        if value:
            qs = Employee.objects.filter(employee_id=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "An employee with this ID already exists."
                )
        return value