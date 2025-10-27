# serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from User.models import AppUser

class AppUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = AppUser
        # include the fields you need - ensure 'password' is present for write
        fields = ['id', 'name', 'email', 'password', 'user_level', 'job_role', 'phone_number']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        user = AppUser.objects.create(**validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.password = make_password(password)
        instance.save()
        return instance
