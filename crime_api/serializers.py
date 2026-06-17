from rest_framework import serializers
from .models import OffenseCategory, District, Incident


class OffenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OffenseCategory
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class IncidentSerializer(serializers.ModelSerializer):
    primary_type = OffenseCategorySerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    primary_type_id = serializers.IntegerField(write_only=True)
    district_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Incident
        fields = [
            'id',
            'case_number',
            'date',
            'block',
            'arrest',
            'domestic',
            'fbi_code',
            'primary_type',
            'district',
            'primary_type_id',
            'district_id',
        ]

    def create(self, validated_data):
        category_id = validated_data.pop('primary_type_id')
        district_id = validated_data.pop('district_id')
        try:
            category = OffenseCategory.objects.get(id=category_id)
        except OffenseCategory.DoesNotExist:
            raise serializers.ValidationError(
                {'primary_type_id': 'OffenseCategory with this ID does not exist.'}
            )
        try:
            district = District.objects.get(id=district_id)
        except District.DoesNotExist:
            raise serializers.ValidationError(
                {'district_id': 'District with this ID does not exist.'}
            )
        incident = Incident.objects.create(
            primary_type=category,
            district=district,
            **validated_data,
        )
        return incident


class ArrestRateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    total = serializers.IntegerField()
    arrests = serializers.IntegerField()
    arrest_rate = serializers.FloatField()


class DistrictSafetySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    district_num = serializers.IntegerField()
    name = serializers.CharField()
    population = serializers.IntegerField()
    incident_count = serializers.IntegerField()
    per_capita_rate = serializers.FloatField()


class TemporalStatsSerializer(serializers.Serializer):
    month = serializers.DateTimeField()
    total = serializers.IntegerField()
    arrests = serializers.IntegerField()
    arrest_rate = serializers.FloatField()
