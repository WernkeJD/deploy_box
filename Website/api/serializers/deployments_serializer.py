from rest_framework import serializers
from ..models import Deployments


class DeploymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deployments
        fields = ["id", "stack", "user", "name"]
