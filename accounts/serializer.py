from rest_framework import serializers
from .models import CustomUser, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()  # Nested serializer for Read/Update

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'profile']

    def update(self, instance, validated_data):
        # Extract profile data from the nested dict
        profile_data = validated_data.pop('profile', None)

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Profile fields (the signal ensures instance.profile exists)
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # create_user hashes the password automatically
        user = CustomUser.objects.create_user(**validated_data)
        return user


class AvatarUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar']