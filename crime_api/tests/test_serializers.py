from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
from rest_framework.test import APITestCase
from crime_api.serializers import (
    IncidentSerializer,
    OffenseCategorySerializer,
    DistrictSerializer,
)
from crime_api.model_factories import (
    IncidentFactory,
    OffenseCategoryFactory,
    DistrictFactory,
)


class OffenseCategorySerializerTests(APITestCase):
    def test_serializer_contains_expected_fields(self):
        category = OffenseCategoryFactory()
        serializer = OffenseCategorySerializer(category)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('code', data)
        self.assertIn('name', data)
        self.assertIn('category', data)

    def test_valid_data_passes_validation(self):
        data = {'code': '051A', 'name': 'Assault', 'category': 'violent'}
        serializer = OffenseCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())


class DistrictSerializerTests(APITestCase):
    def test_serializer_contains_expected_fields(self):
        district = DistrictFactory()
        serializer = DistrictSerializer(district)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('district_num', data)
        self.assertIn('name', data)
        self.assertIn('area_type', data)
        self.assertIn('population', data)

    def test_valid_data_passes_validation(self):
        data = {
            'district_num': 10,
            'name': 'District 10',
            'area_type': 'police',
            'population': 55000,
        }
        serializer = DistrictSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class IncidentSerializerTests(APITestCase):
    def setUp(self):
        self.category = OffenseCategoryFactory()
        self.district = DistrictFactory()

    def test_serialized_output_contains_nested_objects(self):
        incident = IncidentFactory(
            primary_type=self.category,
            district=self.district,
        )
        serializer = IncidentSerializer(incident)
        data = serializer.data
        self.assertIn('primary_type', data)
        self.assertIn('name', data['primary_type'])
        self.assertIn('district', data)
        self.assertIn('district_num', data['district'])

    def test_valid_create_data_passes_validation(self):
        data = {
            'case_number': 'VALID001',
            'date': '2024-06-15T12:00:00Z',
            'block': '100 Main St',
            'arrest': True,
            'domestic': False,
            'fbi_code': '04',
            'primary_type_id': self.category.id,
            'district_id': self.district.id,
        }
        serializer = IncidentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_write_only_fks_fails_validation(self):
        data = {
            'case_number': 'NOFKS001',
            'date': '2024-06-15T12:00:00Z',
            'block': '100 Main St',
            'arrest': False,
            'domestic': False,
            'fbi_code': '04',
        }
        serializer = IncidentSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_create_method_links_foreign_keys(self):
        data = {
            'case_number': 'LINK001',
            'date': '2024-06-15T12:00:00Z',
            'block': '100 Main St',
            'arrest': True,
            'domestic': False,
            'fbi_code': '04',
            'primary_type_id': self.category.id,
            'district_id': self.district.id,
        }
        serializer = IncidentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        incident = serializer.save()
        self.assertEqual(incident.primary_type, self.category)
        self.assertEqual(incident.district, self.district)

    def test_create_fails_with_nonexistent_fk(self):
        data = {
            'case_number': 'BADFK999',
            'date': '2024-06-15T12:00:00Z',
            'block': '100 Main St',
            'arrest': False,
            'domestic': False,
            'fbi_code': '04',
            'primary_type_id': 99999,
            'district_id': self.district.id,
        }
        serializer = IncidentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        from rest_framework import serializers as drf_serializers
        with self.assertRaises(drf_serializers.ValidationError):
            serializer.save()


class HypothesisSerializerTests(HypothesisTestCase):
    """Property-based tests: serializer never crashes on varied valid input."""

    def setUp(self):
        self.category = OffenseCategoryFactory()
        self.district = DistrictFactory()

    @given(
        case_number=st.text(min_size=1, max_size=18),
        date_str=st.dates().map(lambda d: d.isoformat() + 'T12:00:00Z'),
        block=st.text(min_size=1, max_size=190),
        arrest=st.booleans(),
        domestic=st.booleans(),
        fbi_code=st.text(min_size=1, max_size=8),
    )
    @settings(max_examples=50, deadline=None)
    def test_serializer_never_crashes_on_varied_input(
        self, case_number, date_str, block, arrest, domestic, fbi_code
    ):
        data = {
            'case_number': case_number,
            'date': date_str,
            'block': block,
            'arrest': arrest,
            'domestic': domestic,
            'fbi_code': fbi_code,
            'primary_type_id': self.category.id,
            'district_id': self.district.id,
        }
        serializer = IncidentSerializer(data=data)
        is_valid = serializer.is_valid()
        if is_valid:
            incident = serializer.save()
            self.assertIsNotNone(incident.id)
        else:
            self.assertIsNotNone(serializer.errors)
