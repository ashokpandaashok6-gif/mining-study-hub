from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import Question, Subject

bp = Blueprint("questions", __name__, url_prefix="/questions")


@bp.route("/")
def list_questions():
    subject_id = request.args.get("subject", type=int)
    query = Question.query.filter_by(approved=True)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    questions = query.order_by(Question.created_at.desc()).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template(
        "questions/list.html", questions=questions, subjects=subjects, selected_subject=subject_id
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    subjects = Subject.query.order_by(Subject.name).all()

    if request.method == "POST":
        question_text = request.form.get("question", "").strip()
        answer = request.form.get("answer", "").strip()
        subject_id = request.form.get("subject_id", type=int)
        marks = request.form.get("marks", type=int)

        if not question_text:
            flash("The question text is required.", "error")
        else:
            q = Question(
                question=question_text, answer=answer, subject_id=subject_id,
                marks=marks, created_by=current_user.id,
            )
            db.session.add(q)
            db.session.commit()
            flash("Question added to the bank.", "success")
            return redirect(url_for("questions.list_questions"))

    return render_template("questions/new.html", subjects=subjects)


@bp.route("/<int:question_id>/delete", methods=["POST"])
@login_required
def delete(question_id):
    q = Question.query.get_or_404(question_id)
    if q.created_by != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(q)
    db.session.commit()
    flash("Question deleted.", "info")
    return redirect(url_for("questions.list_questions"))
