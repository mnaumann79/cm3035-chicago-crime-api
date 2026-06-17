import factory
from factory.django import DjangoModelFactory
from random import randint, choice
from .models import OffenseCategory, District, Incident


class OffenseCategoryFactory(DjangoModelFactory):
    class Meta:
        model = OffenseCategory

    code = factory.Sequence(lambda n: f'CODE{n:04d}')
    name = factory.Sequence(lambda n: f'Offense Type {n}')
    category = factory.LazyFunction(
        lambda: choice(['violent', 'property', 'quality_of_life'])
    )


class DistrictFactory(DjangoModelFactory):
    class Meta:
        model = District

    district_num = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f'District {n + 1}')
    area_type = factory.LazyFunction(
        lambda: choice(['police', 'community'])
    )
    population = factory.LazyFunction(lambda: randint(30000, 80000))


class IncidentFactory(DjangoModelFactory):
    class Meta:
        model = Incident

    case_number = factory.Sequence(lambda n: f'HY{n:06d}')
    date = factory.Faker('date_time_between', start_date='-2y', end_date='now')
    block = factory.Faker('street_address')
    arrest = factory.LazyFunction(lambda: choice([True, False]))
    domestic = factory.LazyFunction(lambda: choice([True, False]))
    fbi_code = factory.LazyFunction(lambda: f'{randint(1, 26):02d}')
    primary_type = factory.SubFactory(OffenseCategoryFactory)
    district = factory.SubFactory(DistrictFactory)
