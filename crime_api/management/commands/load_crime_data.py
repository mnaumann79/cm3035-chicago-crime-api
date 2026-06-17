import csv
import locale
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from crime_api.models import OffenseCategory, District, Incident

# Force C locale for locale-independent date parsing (AM/PM recognition)
locale.setlocale(locale.LC_TIME, 'C')


DISTRICT_POPULATIONS = {
    1: 45000, 2: 52000, 3: 48000, 4: 55000, 5: 42000,
    6: 50000, 7: 47000, 8: 53000, 9: 44000, 10: 49000,
    11: 51000, 12: 46000, 13: 38000, 14: 54000, 15: 43000,
    16: 56000, 17: 40000, 18: 50000, 19: 48000, 20: 52000,
    21: 45000, 22: 51000, 23: 47000, 24: 49000, 25: 53000,
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
                            'population': DISTRICT_POPULATIONS.get(district_num, 50000),
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
