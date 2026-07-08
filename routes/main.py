from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import PDF, Note, Question, Subject

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    stats = {
        "pdfs": PDF.query.count(),
        "notes": Note.query.count(),
        "questions": Question.query.count(),
        "subjects": Subject.query.count(),
    }
    return render_template("home.html", stats=stats)


@bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "pdfs": PDF.query.count(),
        "notes": Note.query.count(),
        "questions": Question.query.count(),
        "subjects": Subject.query.count(),
    }
    recent_pdfs = PDF.query.order_by(PDF.uploaded_at.desc()).limit(5).all()
    recent_notes = Note.query.order_by(Note.uploaded_at.desc()).limit(5).all()
    return render_template(
        "dashboard.html", stats=stats, recent_pdfs=recent_pdfs, recent_notes=recent_notes
    )
