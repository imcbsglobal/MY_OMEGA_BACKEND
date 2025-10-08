from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class SuperuserIDLoginSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)

    def validate(self, attrs):
        uid = attrs.get('user_id')
        pwd = attrs.get('password')

        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User not found."})

        if not user.is_superuser:
            raise serializers.ValidationError({"detail": "Only superusers are allowed to log in here."})

        if not user.check_password(pwd):
            raise serializers.ValidationError({"password": "Incorrect password."})

        attrs['user'] = user
        return attrs
