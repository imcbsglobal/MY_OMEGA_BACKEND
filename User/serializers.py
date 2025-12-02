# User/serializers.py - COMPLETE UPDATED VERSION WITH IMAGE UPLOAD FIX
from rest_framework import serializers
from .models import AppUser


# --------------------------------------------------------------------
# READ / GET SERIALIZER
# --------------------------------------------------------------------
class AppUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    aadhar_attachment_url = serializers.SerializerMethodField()
    job_title_display = serializers.SerializerMethodField()

    class Meta:
        model = AppUser
        fields = [
            'id','email','username',
            'name','first_name','last_name','dob',
            'photo','photo_url',

            'address','place','district',
            'personal_phone','residential_phone','phone_number',

            'user_level','job_title','job_role','job_title_display',
            'organization','education','experience','joining_date',
            'duty_time_start','duty_time_end',

            'bank_account_number','ifsc_code','bank_name','branch',

            'aadhar_attachment','aadhar_attachment_url',

            'is_active','is_staff','is_superuser',
            'date_joined','created_at','updated_at',
        ]
        read_only_fields = [
            'id','username','first_name','last_name',
            'photo_url','aadhar_attachment_url','job_title_display',
            'created_at','updated_at','is_superuser','date_joined'
        ]

    def get_username(self, obj):
        return obj.email

    def get_first_name(self, obj):
        return obj.name.split()[0] if obj.name else ''

    def get_last_name(self, obj):
        parts = obj.name.split()
        return ' '.join(parts[1:]) if len(parts) > 1 else ''

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None

    def get_aadhar_attachment_url(self, obj):
        if obj.aadhar_attachment:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.aadhar_attachment.url) if request else obj.aadhar_attachment.url
        return None

    def get_job_title_display(self, obj):
        return obj.get_job_title_display()


# --------------------------------------------------------------------
# CREATE SERIALIZER (POST) — UPDATED FOR IMAGE UPLOAD
# --------------------------------------------------------------------
class AppUserCreateSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(
        write_only=True, required=False, allow_null=True
    )

    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}, min_length=6
    )
    confirm_password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )

    class Meta:
        model = AppUser
        fields = [
            'email','password','confirm_password','name',
            'dob','photo','profile_picture',

            'address','place','district','personal_phone',
            'residential_phone','phone_number',

            'user_level','job_title','job_role',
            'organization','education','experience','joining_date',
            'duty_time_start','duty_time_end',

            'bank_account_number','ifsc_code','bank_name','branch',
            'aadhar_attachment',

            'is_active','is_staff',
        ]

    def validate_email(self, value):
        if AppUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, data):
        if data.get("password") != data.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        profile_picture = validated_data.pop("profile_picture", None)

        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password")

        user = AppUser(**validated_data)

        if profile_picture:
            user.photo = profile_picture  # SAVE IMAGE

        user.set_password(password)
        user.save()
        return user


# --------------------------------------------------------------------
# UPDATE SERIALIZER (PUT/PATCH) — UPDATED FOR IMAGE UPLOAD
# --------------------------------------------------------------------
class AppUserUpdateSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(
        write_only=True, required=False, allow_null=True
    )

    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        style={'input_type': 'password'}, min_length=6
    )
    confirm_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = AppUser
        fields = [
            'email','password','confirm_password','name',
            'dob','photo','profile_picture',

            'address','place','district','personal_phone',
            'residential_phone','phone_number',

            'user_level','job_title','job_role',
            'organization','education','experience','joining_date',
            'duty_time_start','duty_time_end',

            'bank_account_number','ifsc_code','bank_name','branch',
            'aadhar_attachment',

            'is_active','is_staff',
        ]

    def validate_email(self, value):
        user = self.instance
        if AppUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if password and password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def update(self, instance, validated_data):
        profile_picture = validated_data.pop("profile_picture", None)

        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if profile_picture:
            instance.photo = profile_picture  # SAVE IMAGE

        if password:
            instance.set_password(password)

        instance.save()
        return instance


# --------------------------------------------------------------------
# OTHER SERIALIZERS (unchanged)
# --------------------------------------------------------------------
class LoginResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
    user_level = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    is_admin = serializers.BooleanField()

    job_role = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    job_title = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    personal_phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    photo_url = serializers.CharField(required=False, allow_null=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, min_length=6, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({'confirm_new_password': 'New passwords do not match.'})
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='name', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = AppUser
        fields = [
            'id','email','name','full_name','job_title',
            'user_level','photo_url','is_active',
        ]

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None
