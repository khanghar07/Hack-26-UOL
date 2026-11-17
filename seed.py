import os
import json
from firebase_admin import auth
from directory import PEOPLE, email_for, password_for
from identity import app, require_configured
from storage import database, initialize


def seed():
    require_configured()
    initialize()
    rows = []
    for reference_uid, name, role, specialization, skills in PEOPLE:
        email = email_for(name)
        password = password_for(name)
        # A web-created admin has a Firebase-generated UID. Preserve that identity.
        if reference_uid == 'ADMIN':
            try:
                user = auth.get_user_by_email(email, app=app)
            except auth.UserNotFoundError:
                try:
                    user = auth.get_user(reference_uid, app=app)
                except auth.UserNotFoundError:
                    user = auth.create_user(uid=reference_uid, email=email, password=password,
                                            display_name=name, app=app)
            if user.email != email or os.getenv('ADMIN_PASSWORD'):
                user = auth.update_user(user.uid, email=email, password=password, app=app)
        else:
            try:
                user = auth.get_user(reference_uid, app=app)
            except auth.UserNotFoundError:
                try:
                    user = auth.create_user(uid=reference_uid, email=email, password=password,
                                            display_name=name, app=app)
                except auth.UidAlreadyExistsError:
                    user = auth.get_user(reference_uid, app=app)
            if user.email != email:
                raise RuntimeError(f'UID {reference_uid} belongs to a different account. Check Firebase project.')
        rows.append((user.uid, name, email, role, specialization, json.dumps(skills)))
    with database() as db:
        # Only replace the previous seeded admin profile; never grant roles at login.
        admin_uid = rows[0][0]
        db.execute("DELETE FROM users WHERE role='ADMIN' AND id<>?", (admin_uid,))
        db.executemany('''INSERT INTO users(id,name,email,role,specialization,skills)
            VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,
            email=excluded.email, role=excluded.role, specialization=excluded.specialization,
            skills=excluded.skills''', rows)
    print(f'Verified {len(rows)} Firebase accounts and saved their profiles.')

if __name__ == '__main__':
    seed()
