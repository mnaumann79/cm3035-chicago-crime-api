"""Build the CM3035 coursework submission ZIP (D1 + D2 + D3)."""
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZIP_NAME = ROOT / 'cm3035_coursework_submission.zip'
TOP_DIR = 'cm3035_coursework_submission'

# Files and directories to include. Each entry is relative to ROOT.
INCLUDE_PATHS = [
    'chicago_crime',
    'crime_api',
    'manage.py',
    'requirements.txt',
    'chicago_crime_data.csv',
    'db.sqlite3',
    'README.md',
    'report.md',
    'report.pdf',
]

# Patterns to exclude anywhere in the tree.
EXCLUDE_SUFFIXES = ('.pyc',)
EXCLUDE_NAMES = {'__pycache__', '.hypothesis', '.git', 'venv', '.venv', 'static'}
EXCLUDE_FILES = {
    'PA_SETUP.md', 'render.yaml', 'resume.md',
    'AWD-CW1.pdf', 'CM3035_Coursework_Rubrics.pdf',
    'cm3035_coursework_submission.zip',  # don't include the zip itself
    'build_zip.py',
}


def should_skip(path: Path) -> bool:
    if path.name in EXCLUDE_FILES:
        return True
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    # Skip nested __pycache__ directories
    if '__pycache__' in path.parts:
        return True
    return False


def main():
    if ZIP_NAME.exists():
        ZIP_NAME.unlink()

    file_count = 0
    total_size = 0

    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel in INCLUDE_PATHS:
            src = ROOT / rel
            if not src.exists():
                print(f'WARN: {rel} does not exist, skipping')
                continue

            if src.is_file():
                arc = f'{TOP_DIR}/{rel}'
                zf.write(src, arc)
                file_count += 1
                total_size += src.stat().st_size
            else:
                for f in src.rglob('*'):
                    if not f.is_file():
                        continue
                    rel_path = f.relative_to(ROOT)
                    if should_skip(rel_path):
                        continue
                    arc = f'{TOP_DIR}/{rel_path}'
                    zf.write(f, arc)
                    file_count += 1
                    total_size += f.stat().st_size

    print(f'Built {ZIP_NAME.name}: {file_count} files, {total_size / 1024:.1f} KB uncompressed')
    print(f'ZIP size: {ZIP_NAME.stat().st_size / 1024:.1f} KB')


if __name__ == '__main__':
    main()
