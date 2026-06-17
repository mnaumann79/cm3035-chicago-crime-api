from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from crime_api.model_factories import (
    IncidentFactory,
    OffenseCategoryFactory,
    DistrictFactory,
)
from crime_api.models import Incident, OffenseCategory, District


class IncidentListTests(APITestCase):
    def setUp(self):
        self.category = OffenseCategoryFactory(name='Theft')
        self.district = DistrictFactory(name='Test District')
        for i in range(5):
            IncidentFactory(
                primary_type=self.category,
                district=self.district,
            )
        self.url = reverse('incident-list')

    def tearDown(self):
        Incident.objects.all().delete()
        OffenseCategory.objects.all().delete()
        District.objects.all().delete()

    def test_list_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_all_incidents(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), 5)

    def test_list_filters_by_category(self):
        response = self.client.get(self.url + '?category=Theft')
        self.assertEqual(len(response.data['results']), 5)
        response = self.client.get(self.url + '?category=Nonexistent')
        self.assertEqual(len(response.data['results']), 0)

    def test_list_filters_by_arrest(self):
        response = self.client.get(self.url + '?arrest=true')
        for item in response.data['results']:
            self.assertTrue(item['arrest'])

    def test_list_structure_includes_nested_data(self):
        response = self.client.get(self.url)
        item = response.data['results'][0]
        self.assertIn('primary_type', item)
        self.assertIn('district', item)
        self.assertIn('name', item['primary_type'])

    def test_post_creates_incident_returns_201(self):
        data = {
            'case_number': 'TEST001',
            'date': '2024-01-15T12:00:00Z',
            'block': '100 Main St',
            'arrest': True,
            'domestic': False,
            'fbi_code': '04',
            'primary_type_id': self.category.id,
            'district_id': self.district.id,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Incident.objects.count(), 6)

    def test_post_missing_required_fields_returns_400(self):
        data = {'case_number': 'INCOMPLETE'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_foreign_key_returns_400(self):
        data = {
            'case_number': 'BADFK001',
            'date': '2024-01-15T12:00:00Z',
            'block': '100 Main St',
            'arrest': False,
            'domestic': False,
            'fbi_code': '04',
            'primary_type_id': 99999,
            'district_id': self.district.id,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IncidentDetailTests(APITestCase):
    def setUp(self):
        self.category = OffenseCategoryFactory()
        self.district = DistrictFactory()
        self.incident = IncidentFactory(
            primary_type=self.category,
            district=self.district,
        )
        self.url = reverse('incident-detail', args=[self.incident.id])

    def tearDown(self):
        Incident.objects.all().delete()
        OffenseCategory.objects.all().delete()
        District.objects.all().delete()

    def test_detail_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_includes_nested_serializers(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.data['primary_type']['name'],
            self.category.name,
        )

    def test_detail_404_for_missing_id(self):
        url = reverse('incident-detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_404_for_bad_id_format(self):
        response = self.client.get('/api/incidents/abc/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_returns_204(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Incident.objects.count(), 0)


class ArrestRatesTests(APITestCase):
    def setUp(self):
        self.category = OffenseCategoryFactory(name='Burglary')
        self.district = DistrictFactory()
        IncidentFactory.create_batch(
            4,
            primary_type=self.category,
            district=self.district,
            arrest=True,
        )
        IncidentFactory(
            primary_type=self.category,
            district=self.district,
            arrest=False,
        )
        self.url = reverse('arrest-rates')

    def tearDown(self):
        Incident.objects.all().delete()
        OffenseCategory.objects.all().delete()
        District.objects.all().delete()

    def test_arrest_rates_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_arrest_rate_calculation(self):
        response = self.client.get(self.url)
        burglary = [s for s in response.data if s['name'] == 'Burglary'][0]
        self.assertEqual(burglary['total'], 5)
        self.assertEqual(burglary['arrests'], 4)


class DistrictSafetyTests(APITestCase):
    def setUp(self):
        self.district = DistrictFactory(population=50000)
        self.category = OffenseCategoryFactory()
        for _ in range(10):
            IncidentFactory(
                primary_type=self.category,
                district=self.district,
            )
        self.url = reverse('district-safety')

    def tearDown(self):
        Incident.objects.all().delete()
        OffenseCategory.objects.all().delete()
        District.objects.all().delete()

    def test_district_safety_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_per_capita_rate_positive(self):
        response = self.client.get(self.url)
        entry = response.data[0]
        self.assertGreaterEqual(entry['per_capita_rate'], 0)
        self.assertEqual(entry['incident_count'], 10)


class TemporalStatsTests(APITestCase):
    def setUp(self):
        self.category = OffenseCategoryFactory()
        self.district = DistrictFactory()
        IncidentFactory(
            primary_type=self.category,
            district=self.district,
            date='2024-06-15T12:00:00Z',
            arrest=True,
        )
        IncidentFactory(
            primary_type=self.category,
            district=self.district,
            date='2024-06-20T12:00:00Z',
            arrest=False,
        )
        self.url = reverse('temporal-stats')

    def tearDown(self):
        Incident.objects.all().delete()
        OffenseCategory.objects.all().delete()
        District.objects.all().delete()

    def test_temporal_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_monthly_aggregation(self):
        response = self.client.get(self.url)
        month = [s for s in response.data if s['month'] and s['month'].strftime('%Y-%m') == '2024-06'][0]
        self.assertEqual(month['total'], 2)
        self.assertEqual(month['arrests'], 1)

    def test_arrest_rate_in_valid_range(self):
        response = self.client.get(self.url)
        for entry in response.data:
            self.assertGreaterEqual(entry['arrest_rate'], 0.0)
            self.assertLessEqual(entry['arrest_rate'], 100.0)


class ApiRootTests(APITestCase):
    def setUp(self):
        self.url = reverse('api-root')

    def test_api_root_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_root_contains_endpoint_links(self):
        response = self.client.get(self.url)
        content = response.content.decode()
        self.assertIn('Incidents List', content)
        self.assertIn('Arrest Rates', content)
        self.assertIn('href=', content)

    def test_api_root_shows_metadata(self):
        response = self.client.get(self.url)
        content = response.content.decode()
        self.assertIn('Django Version', content)
        self.assertIn('admin', content)
