from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import User, Subject, PDF, Note, Question
from utils.decorators import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@login_required
@admin_required
def panel():
    stats = {
        "users": User.query.count(),
        "pdfs": PDF.query.count(),
        "notes": Note.query.count(),
        "questions": Question.query.count(),
        "subjects": Subject.query.count(),
        "pending_pdfs": PDF.query.filter_by(approved=False).count(),
        "pending_notes": Note.query.filter_by(approved=False).count(),
        "pending_questions": Question.query.filter_by(approved=False).count(),
    }
    pending_pdfs = PDF.query.filter_by(approved=False).all()
    pending_notes = Note.query.filter_by(approved=False).all()
    pending_questions = Question.query.filter_by(approved=False).all()
    return render_template(
        "admin/panel.html", stats=stats,
        pending_pdfs=pending_pdfs, pending_notes=pending_notes, pending_questions=pending_questions,
    )


@bp.route("/subjects", methods=["GET", "POST"])
@login_required
@admin_required
def subjects():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name and not Subject.query.filter_by(name=name).first():
            db.session.add(Subject(name=name))
            db.session.commit()
            flash("Subject added.", "success")
        else:
            flash("Subject name is required and must be unique.", "error")
        return redirect(url_for("admin.subjects"))

    all_subjects = Subject.query.order_by(Subject.name).all()
    return render_template("admin/subjects.html", subjects=all_subjects)


@bp.route("/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    PDF.query.filter_by(subject_id=subject.id).update({"subject_id": None})
    Note.query.filter_by(subject_id=subject.id).update({"subject_id": None})
    Question.query.filter_by(subject_id=subject.id).update({"subject_id": None})
    db.session.delete(subject)
    db.session.commit()
    flash("Subject removed.", "info")
    return redirect(url_for("admin.subjects"))


@bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"Updated admin status for {user.username}.", "info")
    return redirect(url_for("admin.users"))


@bp.route("/approve/<kind>/<int:item_id>", methods=["POST"])
@login_required
@admin_required
def approve(kind, item_id):
    model_map = {"pdf": PDF, "note": Note, "question": Question}
    model = model_map.get(kind)
    if model is None:
        flash("Unknown item type.", "error")
        return redirect(url_for("admin.panel"))

    item = model.query.get_or_404(item_id)
    item.approved = True
    db.session.commit()
    flash("Item approved.", "success")
    return redirect(url_for("admin.panel"))


@bp.route("/reject/<kind>/<int:item_id>", methods=["POST"])
@login_required
@admin_required
def reject(kind, item_id):
    model_map = {"pdf": PDF, "note": Note, "question": Question}
    model = model_map.get(kind)
    if model is None:
        flash("Unknown item type.", "error")
        return redirect(url_for("admin.panel"))

    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Item rejected and removed.", "info")
    return redirect(url_for("admin.panel"))
