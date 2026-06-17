from django.urls import path
from . import api

urlpatterns = [
    path('', api.api_root, name='api-root'),
    path('incidents/', api.IncidentList.as_view(), name='incident-list'),
    path('incidents/<int:pk>/', api.IncidentDetail.as_view(), name='incident-detail'),
    path('stats/arrest-rates/', api.ArrestRates.as_view(), name='arrest-rates'),
    path('stats/district-safety/', api.DistrictSafety.as_view(), name='district-safety'),
    path('stats/temporal/', api.TemporalStats.as_view(), name='temporal-stats'),
]
