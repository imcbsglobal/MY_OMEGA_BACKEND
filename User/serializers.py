# User/serializers.py

from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import AppUser


class AppUserSerializer(serializers.ModelSerializer):
    """
    Serializer for AppUser creation, listing and updates.

    - photo is required on create (enforced by the model).
    - password is write-only and will be hashed on create/update.
    - user_level limited to Super Admin / Admin / User
    - id and created_at are read-only
    """
    user_level = serializers.ChoiceField(choices=AppUser.Levels.choices)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        required=True,
        help_text="Plain text password. Will be hashed before saving."
    )

    class Meta:
        model = AppUser
        fields = [
            'id', 'photo', 'name', 'user_id', 'password',
            'user_level', 'job_role', 'phone_number', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_user_id(self, value: str) -> str:
        """
        Ensure user_id is unique. When updating, exclude the current instance.
        """
        instance = getattr(self, 'instance', None)
        qs = AppUser.objects.filter(user_id=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This user_id already exists.")
        return value

    def create(self, validated_data):
        """
        Hash the password before saving the AppUser.
        """
        raw_password = validated_data.pop('password')
        validated_data['password'] = make_password(raw_password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Hash password if provided on update. Allow partial updates.
        """
        if 'password' in validated_data:
            raw_password = validated_data.pop('password')
            validated_data['password'] = make_password(raw_password)
        return super().update(instance, validated_data)
