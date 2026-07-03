from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import Note, Subject

bp = Blueprint("notes", __name__, url_prefix="/notes")


@bp.route("/")
def list_notes():
    subject_id = request.args.get("subject", type=int)
    query = Note.query.filter_by(approved=True)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    notes = query.order_by(Note.created_at.desc()).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template("notes/list.html", notes=notes, subjects=subjects, selected_subject=subject_id)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    subjects = Subject.query.order_by(Subject.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        subject_id = request.form.get("subject_id", type=int)

        if not title or not content:
            flash("Title and content are required.", "error")
        else:
            note = Note(title=title, content=content, subject_id=subject_id, created_by=current_user.id)
            db.session.add(note)
            db.session.commit()
            flash("Note published.", "success")
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
    if note.created_by != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "info")
    return redirect(url_for("notes.list_notes"))
