# User/serializers.py - COMPLETE VERSION WITH ALL EMPLOYEE FIELDS
from rest_framework import serializers
from .models import AppUser


class AppUserSerializer(serializers.ModelSerializer):
    """
    Complete serializer for AppUser with all employee fields
    Used for GET requests (list and retrieve)
    """
    
    # Computed/Read-only fields
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    aadhar_attachment_url = serializers.SerializerMethodField()
    job_title_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AppUser
        fields = [
            # ========== IDs and Authentication ==========
            'id',
            'email',
            'username',  # computed from email
            
            # ========== Personal Information ==========
            'name',
            'first_name',  # computed from name
            'last_name',   # computed from name
            'dob',
            'photo',
            'photo_url',   # computed URL
            
            # ========== Contact Information ==========
            'address',
            'place',
            'district',
            'personal_phone',
            'residential_phone',
            'phone_number',  # legacy field
            
            # ========== Professional Information ==========
            'user_level',
            'job_title',
            'job_role',
            'job_title_display',  # computed
            'organization',
            'education',
            'experience',
            'joining_date',
            'duty_time_start',
            'duty_time_end',
            
            # ========== Financial Information ==========
            'bank_account_number',
            'ifsc_code',
            'bank_name',
            'branch',
            
            # ========== Documents ==========
            'aadhar_attachment',
            'aadhar_attachment_url',  # computed URL
            
            # ========== System Fields ==========
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 
            'date_joined', 
            'username', 
            'first_name', 
            'last_name', 
            'photo_url',
            'aadhar_attachment_url',
            'job_title_display',
            'created_at', 
            'updated_at',
            'is_superuser',  # Only settable via admin
        ]
    
    def get_username(self, obj):
        """Return email as username for compatibility"""
        return obj.email
    
    def get_first_name(self, obj):
        """Extract first name from name field"""
        return obj.name.split()[0] if obj.name else ''
    
    def get_last_name(self, obj):
        """Extract last name from name field"""
        parts = obj.name.split()
        return ' '.join(parts[1:]) if len(parts) > 1 else ''
    
    def get_photo_url(self, obj):
        """Return full URL for photo"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def get_aadhar_attachment_url(self, obj):
        """Return full URL for aadhar attachment"""
        if obj.aadhar_attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhar_attachment.url)
            return obj.aadhar_attachment.url
        return None
    
    def get_job_title_display(self, obj):
        """Return job_title if available, otherwise job_role"""
        return obj.get_job_title_display()


class AppUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users with all employee fields
    Used for POST requests
    """
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        min_length=6,
        help_text='Password (minimum 6 characters)'
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        help_text='Confirm password'
    )
    
    class Meta:
        model = AppUser
        fields = [
            # ========== Authentication (Required) ==========
            'email',
            'password',
            'confirm_password',
            'name',
            
            # ========== Personal Information ==========
            'dob',
            'photo',
            
            # ========== Contact Information ==========
            'address',
            'place',
            'district',
            'personal_phone',
            'residential_phone',
            'phone_number',
            
            # ========== Professional Information ==========
            'user_level',
            'job_title',
            'job_role',
            'organization',
            'education',
            'experience',
            'joining_date',
            'duty_time_start',
            'duty_time_end',
            
            # ========== Financial Information ==========
            'bank_account_number',
            'ifsc_code',
            'bank_name',
            'branch',
            
            # ========== Documents ==========
            'aadhar_attachment',
            
            # ========== System Fields ==========
            'is_active',
            'is_staff',
        ]
        extra_kwargs = {
            'name': {'required': True},
        }
    
    def validate_email(self, value):
        """Check if email already exists"""
        if AppUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()  # Store emails in lowercase
    
    def validate(self, data):
        """Validate password match"""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data
    
    def create(self, validated_data):
        # Remove confirm_password before creating user
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        
        # Create user instance
        user = AppUser(**validated_data)
        user.set_password(password)  # Hash the password
        user.save()
        
        return user


class AppUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating users with all employee fields
    Used for PUT/PATCH requests
    """
    
    password = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_blank=True,
        style={'input_type': 'password'},
        min_length=6,
        help_text='New password (leave blank to keep current password)'
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=False,
        allow_blank=True,
        style={'input_type': 'password'},
        help_text='Confirm new password'
    )
    
    class Meta:
        model = AppUser
        fields = [
            # ========== Authentication ==========
            'email',
            'password',
            'confirm_password',
            'name',
            
            # ========== Personal Information ==========
            'dob',
            'photo',
            
            # ========== Contact Information ==========
            'address',
            'place',
            'district',
            'personal_phone',
            'residential_phone',
            'phone_number',
            
            # ========== Professional Information ==========
            'user_level',
            'job_title',
            'job_role',
            'organization',
            'education',
            'experience',
            'joining_date',
            'duty_time_start',
            'duty_time_end',
            
            # ========== Financial Information ==========
            'bank_account_number',
            'ifsc_code',
            'bank_name',
            'branch',
            
            # ========== Documents ==========
            'aadhar_attachment',
            
            # ========== System Fields ==========
            'is_active',
            'is_staff',
        ]
    
    def validate_email(self, value):
        """Check if email is taken by another user"""
        user = self.instance
        if AppUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, data):
        """Validate password match if password is being changed"""
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # If password is provided, confirm_password must match
        if password and password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        return data
    
    def update(self, instance, validated_data):
        # Remove password fields
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for login response - only essential fields
    Used in login_view response
    """
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
    user_level = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    is_admin = serializers.BooleanField()
    
    # Optional profile fields
    job_role = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    job_title = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    personal_phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    photo_url = serializers.CharField(required=False, allow_null=True)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        style={'input_type': 'password'}
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({
                'confirm_new_password': 'New passwords do not match.'
            })
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class UserBriefSerializer(serializers.ModelSerializer):
    """
    Brief serializer for listing users (minimal fields)
    Use this for dropdowns, selects, or user lists
    """
    full_name = serializers.CharField(source='name', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AppUser
        fields = [
            'id',
            'email',
            'name',
            'full_name',
            'job_title',
            'user_level',
            'photo_url',
            'is_active',
        ]
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None