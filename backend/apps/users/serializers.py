from rest_framework import serializers

from .models import CreatorProfile, User


class CreatorProfileSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = CreatorProfile
        fields = ['category', 'is_verified']


class UserSerializer(serializers.ModelSerializer):
    creator_profile = CreatorProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'display_name', 'bio', 'avatar',
            'avatar_position_x', 'avatar_position_y',
            'is_creator', 'creator_profile',
        ]
        read_only_fields = ['id', 'email', 'is_creator']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'display_name', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data, is_active=False)
        user.set_password(password)
        user.save()
        return user