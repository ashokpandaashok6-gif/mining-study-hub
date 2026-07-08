from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Note, Subject
from routes.pdfs import allowed_pdf, delete_cloudinary_asset, save_pdf_locally, store_pdf_file
import uuid

bp = Blueprint("notes", __name__, url_prefix="/notes")


@bp.route("/")
def list_notes():
    subject_id = request.args.get("subject", type=int)
    semester = request.args.get("semester", type=int)
    query = Note.query.filter_by(approved=True)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if semester:
        query = query.filter_by(semester=semester)
    notes = query.order_by(Note.uploaded_at.desc()).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template(
        "notes/list.html",
        notes=notes,
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
            fallback_path = None
            if warning_message:
                flash(warning_message, "warning")
                fallback_path = save_pdf_locally(file, unique_name)
                cloudinary_url = ""
                public_id = ""
            note = Note(
                title=title,
                subject_id=subject_id,
                semester=semester,
                cloudinary_url=cloudinary_url or f"/uploads/pdfs/{fallback_path or unique_name}",
                public_id=public_id or (fallback_path or unique_name),
                uploaded_by=current_user.id,
            )
            db.session.add(note)
            db.session.commit()
            flash("Note uploaded successfully.", "success")
            return redirect(url_for("notes.view", note_id=note.id))

    return render_template("notes/new.html", subjects=subjects)


@bp.route("/<int:note_id>")
def view(note_id):
    note = Note.query.get_or_404(note_id)
    return render_template("notes/view.html", note=note)


@bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete(note_id):
    note = Note.query.get_or_404(note_id)
    if note.uploaded_by != current_user.id and not current_user.is_admin:
        abort(403)
    if getattr(note, "public_id", None):
        delete_cloudinary_asset(note.public_id)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "info")
    return redirect(url_for("notes.list_notes"))
