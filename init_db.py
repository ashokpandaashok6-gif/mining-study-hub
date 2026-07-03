"""
Run this once to set up the database with starter subjects:
    python init_db.py
"""
from app import create_app
from extensions import db
from models import Subject

DEFAULT_SUBJECTS = [
    "Mine Survey",
    "Mine Ventilation",
    "Mine Machinery",
    "Mining Geology",
    "Rock Mechanics",
    "Mine Environment & Ventilation",
    "Mineral Processing",
    "Mine Legislation",
    "Blasting & Explosives",
    "Mine Support Systems",
]

app = create_app()

with app.app_context():
    db.create_all()
    added = 0
    for name in DEFAULT_SUBJECTS:
        if not Subject.query.filter_by(name=name).first():
            db.session.add(Subject(name=name))
            added += 1
    db.session.commit()
    print(f"Database ready. Added {added} new subject(s).")
    print("Register your first account at /register — it will automatically become admin.")
