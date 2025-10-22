from rest_framework import serializers
from .models import SvgFile

class SvgFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SvgFile
        fields = ['id', 'title_name', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']