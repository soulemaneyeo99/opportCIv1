from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, RegexValidator, FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from ..models import UserProfile, validate_file_size

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    interests = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    certifications = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'skills', 'interests', 'languages', 'certifications',
            'cv', 'linkedin_profile', 'github_profile', 'portfolio_website',
            'availability_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_skills(self, obj):
        return [skill.strip() for skill in obj.skills.split(',') if skill.strip()] if obj.skills else []

    def get_interests(self, obj):
        return [interest.strip() for interest in obj.interests.split(',') if interest.strip()] if obj.interests else []

    def get_languages(self, obj):
        return [lang.strip() for lang in obj.languages.split(',') if lang.strip()] if obj.languages else []

    def get_certifications(self, obj):
        return [cert.strip() for cert in obj.certifications.split(',') if cert.strip()] if obj.certifications else []

    def to_internal_value(self, data):
        # Convertit les listes en chaînes pour stockage
        for field in ['skills', 'interests', 'languages', 'certifications']:
            if isinstance(data.get(field), list):
                data[field] = ', '.join([item.strip() for item in data[field] if item.strip()])
        return super().to_internal_value(data)


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    education_level_display = serializers.CharField(source='get_education_level_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'user_type', 'user_type_display',
            'first_name', 'last_name', 'phone_number', 'profile_picture',
            'city', 'country', 'education_level', 'education_level_display',
            'institution', 'field_of_study', 'is_verified', 'profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    confirm_password = serializers.CharField(write_only=True, required=True)
    terms = serializers.BooleanField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'confirm_password', 'user_type',
            'first_name', 'last_name', 'phone_number', 'city', 'country',
            'education_level', 'institution', 'field_of_study', 'profile',
            'terms'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_username(self, value):
        if not value.replace('_', '').replace('.', '').isalnum():
            raise serializers.ValidationError(
                _("Le nom d'utilisateur ne peut contenir que des lettres, chiffres, _ ou .")
            )
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _("Les mots de passe ne correspondent pas.")
            })

        if not data.get('terms'):
            raise serializers.ValidationError({
                'terms': _("Vous devez accepter les conditions d'utilisation.")
            })

        if data.get('user_type') == User.UserType.STUDENT:
            if not data.get('education_level'):
                raise serializers.ValidationError({
                    'education_level': _("Le niveau d'éducation est requis pour les étudiants.")
                })
            if not data.get('institution'):
                raise serializers.ValidationError({
                    'institution': _("L'établissement d'enseignement est requis pour les étudiants.")
                })

        return data

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        validated_data.pop('terms', None)
        validated_data.pop('confirm_password', None)

        user = User.objects.create_user(
            email=validated_data.pop('email'),
            username=validated_data.pop('username'),
            password=validated_data.pop('password'),
            **validated_data
        )

        if profile_data:
            profile_serializer = UserProfileSerializer(
                instance=user.profile,
                data=profile_data,
                partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'phone_number', 'city', 'country', 'education_level',
            'institution', 'field_of_study'
        ]
        extra_kwargs = {
            'email': {'read_only': True},
            'username': {'read_only': True},
        }

    def validate(self, data):
        if self.instance.user_type == User.UserType.STUDENT:
            if 'education_level' in data and not data['education_level']:
                raise serializers.ValidationError({
                    'education_level': _("Le niveau d'éducation est requis pour les étudiants.")
                })
            if 'institution' in data and not data['institution']:
                raise serializers.ValidationError({
                    'institution': _("L'établissement d'enseignement est requis pour les étudiants.")
                })
        return data


class ProfilePictureUploadSerializer(serializers.Serializer):
    profile_picture = serializers.ImageField(
        required=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size
        ]
    )


class UserLoginSerializer(serializers.Serializer):
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

        if not user:
            raise serializers.ValidationError(
                _("Identifiants invalides. Veuillez réessayer."),
                code='invalid_credentials'
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                _("Identifiants invalides. Veuillez réessayer."),
                code='invalid_credentials'
            )

        if not user.is_verified:
            raise serializers.ValidationError(
                _("Votre compte n'est pas encore vérifié. Veuillez vérifier votre email."),
                code='account_unverified'
            )

        attrs['user'] = user
        return attrs
