import os
from flask import Flask
from flask_login import LoginManager

from config import Config
from extensions import db, login_manager, csrf
from models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["PDF_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["IMAGE_UPLOAD_FOLDER"], exist_ok=True)

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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
