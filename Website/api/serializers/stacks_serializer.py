from rest_framework import serializers
from ..models import Stacks


class StacksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stacks

        depth = 1
        fields = "__all__"
