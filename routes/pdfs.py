import os
import uuid
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    send_from_directory, current_app, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import PDF, Subject

bp = Blueprint("pdfs", __name__, url_prefix="/pdfs")


def allowed_pdf(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_PDF_EXTENSIONS"]
    )


@bp.route("/")
def list_pdfs():
    subject_id = request.args.get("subject", type=int)
    query = PDF.query.filter_by(approved=True)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    pdfs = query.order_by(PDF.uploaded_at.desc()).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template("pdfs/list.html", pdfs=pdfs, subjects=subjects, selected_subject=subject_id)


@bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
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
            file.save(os.path.join(current_app.config["PDF_UPLOAD_FOLDER"], unique_name))

            pdf = PDF(
                title=title,
                subject_id=subject_id,
                semester=semester,
                filename=unique_name,
                uploaded_by=current_user.id,
            )
            db.session.add(pdf)
            db.session.commit()
            flash("PDF uploaded successfully.", "success")
            return redirect(url_for("pdfs.list_pdfs"))

    return render_template("pdfs/upload.html", subjects=subjects)


@bp.route("/<int:pdf_id>")
def view(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    return render_template("pdfs/view.html", pdf=pdf)


@bp.route("/<int:pdf_id>/file")
def serve_file(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    return send_from_directory(current_app.config["PDF_UPLOAD_FOLDER"], pdf.filename)


@bp.route("/<int:pdf_id>/download")
def download(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    return send_from_directory(
        current_app.config["PDF_UPLOAD_FOLDER"], pdf.filename,
        as_attachment=True, download_name=f"{pdf.title}.pdf"
    )


@bp.route("/<int:pdf_id>/delete", methods=["POST"])
@login_required
def delete(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    if pdf.uploaded_by != current_user.id and not current_user.is_admin:
        abort(403)

    file_path = os.path.join(current_app.config["PDF_UPLOAD_FOLDER"], pdf.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(pdf)
    db.session.commit()
    flash("PDF deleted.", "info")
    return redirect(url_for("pdfs.list_pdfs"))
