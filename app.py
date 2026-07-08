import os
import cloudinary
from flask import Flask
from flask_login import LoginManager
from sqlalchemy import inspect, text

from config import Config
from extensions import db, login_manager, csrf
from models import User, Subject, PDF, Note, Question

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
    "MLGS",
    "Mine Hazards",
    "Surface Mining Technology",
    "Underground Coal Mines",
    "Mine Mechanics",
]


def ensure_schema_columns(app):
    with app.app_context():
        inspector = inspect(db.engine)
        for model in (PDF, Note, Question):
            table_name = model.__tablename__
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column in model.__table__.columns:
                if column.name in existing_columns:
                    continue
                try:
                    column_type = column.type.compile(dialect=db.engine.dialect)
                    db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type}'))
                except Exception as exc:
                    app.logger.warning("Could not add column %s to %s: %s", column.name, table_name, exc)
        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["PDF_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["IMAGE_UPLOAD_FOLDER"], exist_ok=True)

    if app.config.get("CLOUDINARY_CLOUD_NAME") and app.config.get("CLOUDINARY_API_KEY") and app.config.get("CLOUDINARY_API_SECRET"):
        cloudinary.config(
            cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
            api_key=app.config["CLOUDINARY_API_KEY"],
            api_secret=app.config["CLOUDINARY_API_SECRET"],
            secure=True,
        )

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.main import bp as main_bp
    from routes.auth import bp as auth_bp
    from routes.pdfs import bp as pdfs_bp
    from routes.notes import bp as notes_bp
    from routes.questions import bp as questions_bp
    from routes.search import bp as search_bp
    from routes.ai import bp as ai_bp
    from routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pdfs_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        ensure_schema_columns(app)
        if Subject.query.count() == 0:
            for name in DEFAULT_SUBJECTS:
                db.session.add(Subject(name=name))
            db.session.commit()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
