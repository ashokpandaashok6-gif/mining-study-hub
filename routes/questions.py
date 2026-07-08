from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Question, Subject
from routes.pdfs import allowed_pdf, delete_cloudinary_asset, store_pdf_file
import uuid

bp = Blueprint("questions", __name__, url_prefix="/questions")


@bp.route("/")
def list_questions():
    subject_id = request.args.get("subject", type=int)
    semester = request.args.get("semester", type=int)
    query = Question.query.filter_by(approved=True)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if semester:
        query = query.filter_by(semester=semester)
    questions = query.order_by(Question.uploaded_at.desc()).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template(
        "questions/list.html",
        questions=questions,
        subjects=subjects,
        selected_subject=subject_id,
        selected_semester=semester,
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    subjects = Subject.query.order_by(Subject.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject_id = request.form.get("subject_id", type=int)
        semester = request.form.get("semester", type=int)
        file = request.files.get("file")

        if not title or not file or file.filename == "":
            flash("Title and a PDF file are required.", "error")
        elif not allowed_pdf(file.filename):
            flash("Only PDF files are allowed.", "error")
        else:
            safe_name = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{safe_name}"
            cloudinary_url, public_id, warning_message = store_pdf_file(file, unique_name)
            if warning_message:
                flash(warning_message, "warning")
            q = Question(
                title=title,
                subject_id=subject_id,
                semester=semester,
                cloudinary_url=cloudinary_url or unique_name,
                public_id=public_id or unique_name,
                uploaded_by=current_user.id,
            )
            db.session.add(q)
            db.session.commit()
            flash("Question bank PDF uploaded successfully.", "success")
            return redirect(url_for("questions.view", question_id=q.id))

    return render_template("questions/new.html", subjects=subjects)


@bp.route("/<int:question_id>")
def view(question_id):
    q = Question.query.get_or_404(question_id)
    return render_template("questions/view.html", question=q)


@bp.route("/<int:question_id>/delete", methods=["POST"])
@login_required
def delete(question_id):
    q = Question.query.get_or_404(question_id)
    if q.uploaded_by != current_user.id and not current_user.is_admin:
        abort(403)
    if getattr(q, "public_id", None):
        delete_cloudinary_asset(q.public_id)
    db.session.delete(q)
    db.session.commit()
    flash("Question bank PDF deleted.", "info")
    return redirect(url_for("questions.list_questions"))
