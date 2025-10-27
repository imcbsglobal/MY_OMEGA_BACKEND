from rest_framework import serializers
from .models import AppUser
from django.contrib.auth.hashers import make_password

class AppUserSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False, allow_null=True, use_url=True)
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = AppUser
        fields = [
            'id', 'photo', 'name', 'email', 'password',
            'user_level', 'job_role', 'phone_number', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        # Hash the password before saving
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        # If password is present, hash it
        password = validated_data.pop('password', None)
        if password:
            instance.password = make_password(password)
        # handle photo: if null passed and you want to remove photo, allow that
        return super().update(instance, validated_data)