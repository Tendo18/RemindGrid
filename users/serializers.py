from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'currency', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']


class TokenSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    refresh = serializers.CharField()
    access = serializers.CharField()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label='Confirm Password')

    class Meta:
        model = User
        fields = ['email', 'display_name', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with that email already exists."})

        if len(data['password']) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()