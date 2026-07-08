from flask import Blueprint, render_template, request

from models import PDF, Note, Question, Subject

bp = Blueprint("search", __name__)


@bp.route("/search")
def search():
    term = request.args.get("q", "").strip()
    results = {"pdfs": [], "notes": [], "questions": []}

    if term:
        like = f"%{term}%"
        results["pdfs"] = PDF.query.filter(PDF.title.ilike(like), PDF.approved == True).all()
        results["notes"] = Note.query.filter(Note.title.ilike(like), Note.approved == True).all()
        results["questions"] = Question.query.filter(
            Question.title.ilike(like),
            Question.approved == True,
        ).all()

    subjects = Subject.query.order_by(Subject.name).all()
    total = len(results["pdfs"]) + len(results["notes"]) + len(results["questions"])
    return render_template("search.html", term=term, results=results, total=total, subjects=subjects)
