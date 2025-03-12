from rest_framework import serializers
from ..models import Stacks


class StacksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stacks
        fields = "__all__"
