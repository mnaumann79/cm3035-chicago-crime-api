import csv
import locale
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from crime_api.models import OffenseCategory, District, Incident

# Force C locale for locale-independent date parsing (AM/PM recognition)
locale.setlocale(locale.LC_TIME, 'C')


# Chicago police districts do not publish per-district population figures. As a
# proxy, the loader seeds each District record with the population of a Chicago
# community area of the same numeric id. These values come from the US Census
# Bureau American Community Survey (ACS) 5-year estimates aggregated to
# community areas, as republished on the City of Chicago Open Data Portal
# ("ACS 5-Year Data by Community Area",
# https://data.cityofchicago.org/Community-Economic-Development/ACS-5-Year-Data-by-Community-Area/t68z-cikk)
# and tabulated on Wikipedia
# (https://en.wikipedia.org/wiki/Community_areas_of_Chicago, retrieved 2026).
#
# Note: Chicago's 77 community areas and 22 police districts are NOT a
# one-to-one mapping. Police district 1 does not actually correspond to
# community area 1 (Rogers Park). The values below are documented placeholders
# so the per-capita endpoint produces real-feeling outputs; absolute per-capita
# rates for any individual district should be treated as illustrative, not
# authoritative. The Dictionary of Geographic Names (the authoritative police
# district boundaries) does not publish resident counts.
COMMUNITY_AREA_POPULATION_PROXIES = {
    1: 54173, 2: 78373, 3: 56344, 4: 41651, 5: 36014,
    6: 102827, 7: 67987, 8: 107331, 9: 11558, 10: 39840,
    11: 26649, 12: 19901, 13: 18356, 14: 45538, 15: 63031,
    16: 53332, 17: 41233, 18: 14280, 19: 72088, 20: 22576,
    21: 35533, 22: 71192, 23: 56153, 24: 88164, 25: 97452,
}


class Command(BaseCommand):
    help = 'Load Chicago crime data from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_path = options['csv_file']

        categories_seen = {}
        districts_seen = {}
        incidents_created = 0
        skip_date = 0
        skip_case = 0
        skip_create = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if incidents_created >= 9500:
                    break

                iucr = row.get('IUCR', '').strip()
                primary_type = row.get('Primary Type', '').strip()

                if primary_type not in categories_seen:
                    cat, _ = OffenseCategory.objects.get_or_create(
                        code=iucr if iucr else primary_type[:10],
                        defaults={
                            'name': primary_type if primary_type else 'Unknown',
                            'category': self._classify_category(primary_type),
                        },
                    )
                    categories_seen[primary_type] = cat
                category = categories_seen[primary_type]

                district_num_str = row.get('District', '0').strip()
                try:
                    district_num = int(float(district_num_str))
                except (ValueError, TypeError):
                    district_num = 0

                if district_num not in districts_seen:
                    dist, _ = District.objects.get_or_create(
                        district_num=district_num,
                        defaults={
                            'name': f'District {district_num}',
                            'area_type': 'police',
                            'population': COMMUNITY_AREA_POPULATION_PROXIES.get(district_num, 50000),
                        },
                    )
                    districts_seen[district_num] = dist
                district = districts_seen[district_num]

                date_str = row.get('Date', '').strip()
                try:
                    incident_date = timezone.make_aware(
                        datetime.strptime(date_str, '%m/%d/%Y %I:%M:%S %p')
                    )
                except ValueError:
                    skip_date += 1
                    continue

                arrest = row.get('Arrest', '').strip().lower() == 'true'
                domestic = row.get('Domestic', '').strip().lower() == 'true'

                case_number = row.get('Case Number', '').strip()
                if not case_number:
                    skip_case += 1
                    continue

                fbi_code = row.get('FBI Code', '').strip()
                block = row.get('Block', '').strip()

                try:
                    Incident.objects.create(
                        case_number=case_number,
                        date=incident_date,
                        block=block if block else 'Unknown',
                        arrest=arrest,
                        domestic=domestic,
                        fbi_code=fbi_code if fbi_code else 'UNK',
                        primary_type=category,
                        district=district,
                    )
                    incidents_created += 1
                except Exception as e:
                    if skip_create == 0:
                        self.stderr.write(f'First create error: {e}')
                    skip_create += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded {incidents_created} incidents '
                f'({len(categories_seen)} categories, {len(districts_seen)} districts). '
                f'Skipped: {skip_date} bad dates, {skip_case} missing case#, {skip_create} create errors.'
            )
        )

    def _classify_category(self, name):
        name_lower = name.lower()
        violent = ['homicide', 'assault', 'battery', 'robbery', 'sexual', 'kidnapping', 'weapon', 'offense involving children']
        property_crimes = ['theft', 'burglary', 'arson', 'damage', 'vandalism', 'motor vehicle', 'stolen']
        for term in violent:
            if term in name_lower:
                return 'violent'
        for term in property_crimes:
            if term in name_lower:
                return 'property'
        return 'quality_of_life'
