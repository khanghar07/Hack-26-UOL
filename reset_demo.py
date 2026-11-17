"""Explicitly reset generated CRM records; retain account profiles."""
import argparse
from storage import database
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--delete-generated-projects',action='store_true',required=True)
p.parse_args()
with database() as db:
    for table in ('tasks','projects','transcript_imports'):
        db.execute('DELETE FROM '+table)
print('Generated projects, tasks and import history cleared. Users retained.')
