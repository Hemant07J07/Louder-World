from rest_framework import serializers

class SubscriptionSerializer(serializers.Serializer):
    event_id = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    consent = serializers.BooleanField(required=True)