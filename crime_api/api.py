from django.db.models import Count, Case, When, F, Q
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_datetime
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from django.shortcuts import render
import sys
import django

from .models import Incident, OffenseCategory, District
from .serializers import (
    IncidentSerializer,
    ArrestRateSerializer,
    DistrictSafetySerializer,
    TemporalStatsSerializer,
)


class IncidentList(generics.ListCreateAPIView):
    """List incidents with filtering, or create a new incident."""
    serializer_class = IncidentSerializer

    def get_queryset(self):
        queryset = Incident.objects.select_related(
            'primary_type', 'district'
        ).all()
        category = self.request.query_params.get('category', None)
        district_name = self.request.query_params.get('district', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        arrest = self.request.query_params.get('arrest', None)

        if category:
            queryset = queryset.filter(
                primary_type__name__icontains=category
            )
        if district_name:
            queryset = queryset.filter(
                district__name__icontains=district_name
            )
        if date_from:
            parsed_from = parse_datetime(date_from)
            if parsed_from is None:
                raise ValidationError({
                    'date_from': 'Use ISO 8601 datetime format (e.g. 2024-01-15T12:00:00Z).'
                })
            queryset = queryset.filter(date__gte=parsed_from)
        if date_to:
            parsed_to = parse_datetime(date_to)
            if parsed_to is None:
                raise ValidationError({
                    'date_to': 'Use ISO 8601 datetime format (e.g. 2024-01-15T12:00:00Z).'
                })
            queryset = queryset.filter(date__lte=parsed_to)
        if arrest is not None:
            queryset = queryset.filter(
                arrest=(arrest.lower() == 'true')
            )

        return queryset


class IncidentDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a single incident by ID."""
    queryset = Incident.objects.select_related(
        'primary_type', 'district'
    ).all()
    serializer_class = IncidentSerializer


class ArrestRates(generics.GenericAPIView):
    """Arrest rate percentage by offense category."""
    serializer_class = ArrestRateSerializer
    # Browsable API requires queryset; the actual data comes from get().
    queryset = OffenseCategory.objects.none()

    def get(self, request):
        stats = (
            OffenseCategory.objects.annotate(
                total=Count('incidents'),
                arrests=Count(
                    'incidents', filter=Q(incidents__arrest=True)
                ),
            )
            .annotate(
                arrest_rate=Case(
                    When(total=0, then=0.0),
                    default=100.0 * F('arrests') / F('total'),
                )
            )
            .values('id', 'name', 'category', 'total', 'arrests', 'arrest_rate')
            .order_by('-arrest_rate')
        )
        return Response(list(stats))


class DistrictSafety(generics.GenericAPIView):
    """Per-capita incident rate by district, ordered most dangerous first."""
    serializer_class = DistrictSafetySerializer
    queryset = District.objects.none()

    def get(self, request):
        stats = (
            District.objects.annotate(
                incident_count=Count('incidents'),
            )
            .annotate(
                per_capita_rate=Case(
                    When(population=0, then=0.0),
                    default=100000.0 * F('incident_count') / F('population'),
                )
            )
            .values(
                'id', 'district_num', 'name', 'population',
                'incident_count', 'per_capita_rate'
            )
            .order_by('-per_capita_rate')
        )
        return Response(list(stats))


class TemporalStats(generics.GenericAPIView):
    """Monthly incident counts with arrest percentage over time."""
    serializer_class = TemporalStatsSerializer
    queryset = Incident.objects.none()

    def get(self, request):
        stats = (
            Incident.objects.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Count('id'))
            .annotate(
                arrests=Count('id', filter=Q(arrest=True))
            )
            .annotate(
                arrest_rate=Case(
                    When(total=0, then=0.0),
                    default=100.0 * F('arrests') / F('total'),
                )
            )
            .values('month', 'total', 'arrests', 'arrest_rate')
            .order_by('month')
        )
        return Response(list(stats))


@api_view(['GET'])
def api_root(request):
    """Main API page — hyperlinked endpoint list with metadata."""
    context = {
        'endpoints': [
            {
                'name': 'Incidents List',
                'url': reverse('incident-list', request=request),
                'methods': 'GET, POST',
                'description': 'List all incidents with filtering. POST to create new.',
            },
            {
                'name': 'Incident Detail',
                'url': reverse('incident-detail', request=request, args=[1]),
                'methods': 'GET, PUT, DELETE',
                'description': 'Retrieve, update, or delete a single incident by ID.',
            },
            {
                'name': 'Arrest Rates by Category',
                'url': reverse('arrest-rates', request=request),
                'methods': 'GET',
                'description': 'Arrest rate percentage for each offense category.',
            },
            {
                'name': 'District Safety Index',
                'url': reverse('district-safety', request=request),
                'methods': 'GET',
                'description': 'Per-capita incident rate by district, ranked most dangerous first.',
            },
            {
                'name': 'Temporal Trends',
                'url': reverse('temporal-stats', request=request),
                'methods': 'GET',
                'description': 'Monthly incident counts with arrest rates over time.',
            },
            {
                'name': 'API Documentation (Swagger)',
                'url': reverse('schema-swagger-ui', request=request),
                'methods': 'GET',
                'description': 'Interactive OpenAPI documentation.',
            },
        ],
        'python_version': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
        'django_version': django.get_version(),
        'packages': [
            'Django',
            'djangorestframework',
            'drf-spectacular',
            'factory-boy',
            'hypothesis',
        ],
        'admin_username': 'admin',
        'admin_password': 'admin123',
    }
    return render(request, 'crime_api/api_root.html', context)
