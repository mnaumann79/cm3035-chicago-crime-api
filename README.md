# Chicago Crime REST API

A Django + Django REST Framework service that loads Chicago crime incident data from CSV into a SQLite3 database and exposes it through six analytical endpoints. Built for CM3035 Advanced Web Development coursework.

## Quick Start

```bash
# 1. Extract the ZIP archive
unzip cm3035_coursework_submission.zip
cd coursework2026

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Load the dataset
python manage.py load_crime_data chicago_crime_data.csv

# 6. Run the tests
python manage.py test crime_api

# 7. Start the development server
python manage.py runserver
```

## URLs

Once the server is running on `http://localhost:8000`:

- API root: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/api/docs/
- OpenAPI schema: http://localhost:8000/api/schema/
- Django admin: http://localhost:8000/admin/

## Admin Credentials

- Username: `admin`
- Password: `admin123`

## Data

The dataset is filtered to the 9,500 most recent records from the City of Chicago Open Data Portal's *Crimes (2001 to Present)* collection. After loading, the database holds 9,499 incidents spread across 27 offense categories and 22 police districts.

## Where to Find Things

- Models: `crime_api/models.py`
- Endpoints and views: `crime_api/api.py`
- URL routing: `crime_api/urls.py` and `chicago_crime/urls.py`
- Serializers: `crime_api/serializers.py`
- Test fixtures: `crime_api/model_factories.py`
- Tests: `crime_api/tests/test_api.py` and `crime_api/tests/test_serializers.py`
- CSV loader: `crime_api/management/commands/load_crime_data.py`
- Settings: `chicago_crime/settings.py`

## Tests

Run the full suite (33 tests across API integration, serializers, and a Hypothesis property-based test):

```bash
python manage.py test crime_api
```

Add `-v 2` for verbose output that prints each test name as it runs.
