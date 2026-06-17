# PythonAnywhere Deployment Guide

## 1. Sign up and open a Bash console

https://www.pythonanywhere.com → Sign up (free) → **Consoles** → **Bash**

## 2. Clone the repo and install

```bash
git clone https://github.com/mnaumann79/cm3035-chicago-crime-api.git
cd cm3035-chicago-crime-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Migrate, load data, create superuser

```bash
python manage.py migrate
python manage.py load_crime_data chicago_crime_data.csv
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
print('Superuser created')
"
```

## 4. Set up the web app

- Go to **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.10** (latest available)
- Click through the defaults

## 5. Configure the web app

On the **Web** tab, set:

| Field | Value |
|-------|-------|
| Source code | `/home/<your-username>/cm3035-chicago-crime-api` |
| Working directory | `/home/<your-username>/cm3035-chicago-crime-api` |
| Virtualenv | `/home/<your-username>/cm3035-chicago-crime-api/venv` |

## 6. Edit the WSGI configuration file

Click the link to your WSGI file (under "Code" section), delete everything, and paste:

```python
import os
import sys

path = '/home/<your-username>/cm3035-chicago-crime-api'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'chicago_crime.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Replace `<your-username>` with your actual PythonAnywhere username (top-right corner).

## 7. Configure static files (for admin CSS)

On the **Web** tab, under **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/<your-username>/cm3035-chicago-crime-api/static/` |

Then in the Bash console:
```bash
cd ~/cm3035-chicago-crime-api
source venv/bin/activate
python manage.py collectstatic --noinput
```

## 8. Reload and test

- Click the green **Reload** button at the top of the Web tab
- Visit `https://<your-username>.pythonanywhere.com/api/`

The app is now live. Admin at `/admin/` with `admin` / `admin123`.
