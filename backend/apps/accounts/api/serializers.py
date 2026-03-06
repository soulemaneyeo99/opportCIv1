"""
OpportuCI - Account Serializers
================================
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from ..models import Profile, validate_file_size

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""

    class Meta:
        model = Profile
        fields = [
            'city', 'education_level', 'field_of_study', 'institution',
            'graduation_year', 'skills', 'interests', 'languages',
            'cv', 'linkedin_url', 'portfolio_url', 'bio',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer de base pour User"""
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone_number', 'profile_picture',
            'is_verified', 'profile', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour User avec profil"""
    profile = ProfileSerializer(read_only=True)
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'user_type', 'user_type_display',
            'phone_number', 'profile_picture',
            'is_verified', 'profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de compte"""
    confirm_password = serializers.CharField(write_only=True, required=True)
    terms = serializers.BooleanField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'user_type',
            'phone_number', 'terms'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _("Les mots de passe ne correspondent pas.")
            })

        if not data.get('terms'):
            raise serializers.ValidationError({
                'terms': _("Vous devez accepter les conditions d'utilisation.")
            })

        return data

    def create(self, validated_data):
        validated_data.pop('terms', None)
        validated_data.pop('confirm_password', None)

        user = User.objects.create_user(
            email=validated_data.pop('email'),
            password=validated_data.pop('password'),
            **validated_data
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du compte"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil"""

    class Meta:
        model = Profile
        fields = [
            'city', 'education_level', 'field_of_study', 'institution',
            'graduation_year', 'skills', 'interests', 'languages',
            'linkedin_url', 'portfolio_url', 'bio'
        ]


class ProfilePictureUploadSerializer(serializers.Serializer):
    """Serializer pour l'upload de photo de profil"""
    profile_picture = serializers.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size
        ]
    )


class CVUploadSerializer(serializers.Serializer):
    """Serializer pour l'upload de CV"""
    cv = serializers.FileField(
        required=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size
        ]
    )


class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        trim_whitespace=False,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not (email and password):
            raise serializers.ValidationError(
                _("Email et mot de passe sont requis."),
                code='missing_credentials'
            )

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError(
                _("Identifiants invalides."),
                code='invalid_credentials'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                _("Ce compte est désactivé."),
                code='account_disabled'
            )

        attrs['user'] = user
        return attrs


# Backward compatibility aliases
UserProfileSerializer = ProfileSerializer
