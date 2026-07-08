import io
import os
import uuid
import cloudinary
import cloudinary.uploader
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename


SUPPORTED_PDF_EXTENSIONS = {"pdf"}

def configure_cloudinary():
    cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME")
    api_key = current_app.config.get("CLOUDINARY_API_KEY")
    api_secret = current_app.config.get("CLOUDINARY_API_SECRET")
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        return True
    if current_app.config.get("CLOUDINARY_URL"):
        cloudinary.config(cloud_name=current_app.config["CLOUDINARY_URL"])
        return True
    return False

from extensions import db
from models import PDF, Subject

bp = Blueprint("pdfs", __name__, url_prefix="/pdfs")


def allowed_pdf(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config.get("ALLOWED_PDF_EXTENSIONS", SUPPORTED_PDF_EXTENSIONS)
    )


def is_remote_storage_reference(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def get_storage_url(item):
    return getattr(item, "cloudinary_url", None) or getattr(item, "filename", None)


def store_pdf_file(file_storage, unique_name):
    if configure_cloudinary():
        try:
            file_storage.stream.seek(0)
            file_bytes = file_storage.read()
            upload_result = cloudinary.uploader.upload(
                io.BytesIO(file_bytes),
                resource_type="raw",
                folder="mining-study-hub/pdfs",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                access_mode="public",
            )
            return upload_result.get("secure_url"), upload_result.get("public_id"), None
        except Exception as exc:
            current_app.logger.exception("Cloudinary PDF upload failed")
            return "", "", f"Cloudinary upload failed: {exc}"

    return "", "", "Cloudinary is not configured for file uploads. Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET." 


def save_pdf_locally(file_storage, unique_name):
    file_path = os.path.join(current_app.config["PDF_UPLOAD_FOLDER"], unique_name)
    file_storage.stream.seek(0)
    file_storage.save(file_path)
    return unique_name


def delete_cloudinary_asset(public_id):
    if not public_id:
        return
    if (
        current_app.config.get("CLOUDINARY_CLOUD_NAME")
        and current_app.config.get("CLOUDINARY_API_KEY")
        and current_app.config.get("CLOUDINARY_API_SECRET")
    ):
        try:
            cloudinary.uploader.destroy(public_id, resource_type="raw")
        except Exception as exc:
            current_app.logger.exception("Cloudinary asset delete failed")
            raise exc


@bp.route("/")
def list_pdfs():
    subject_id = request.args.get("subject", type=int)
    semester = request.args.get("semester", type=int)
    query = PDF.query.filter_by(approved=True)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if semester:
        query = query.filter_by(semester=semester)
    pdfs = query.order_by(PDF.uploaded_at.desc()).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template(
        "pdfs/list.html",
        pdfs=pdfs,
        subjects=subjects,
        selected_subject=subject_id,
        selected_semester=semester,
    )


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
            safe_name = secure_filename(file.filename or "")
            unique_name = f"{uuid.uuid4().hex}_{safe_name}"
            original_filename = safe_name
            cloudinary_url, public_id, warning_message = store_pdf_file(file, unique_name)
            fallback_path = None

            if warning_message:
                flash(warning_message, "warning")
                fallback_path = save_pdf_locally(file, unique_name)
                cloudinary_url = ""
                public_id = ""

            pdf = PDF(
                title=title,
                subject_id=subject_id,
                semester=semester,
                filename=original_filename,
                cloudinary_url=cloudinary_url or f"/uploads/pdfs/{fallback_path or unique_name}",
                public_id=public_id or (fallback_path or unique_name),
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
    storage_url = get_storage_url(pdf)
    if is_remote_storage_reference(storage_url):
        return redirect(storage_url)
    return redirect(storage_url or url_for("pdfs.list_pdfs"))


@bp.route("/<int:pdf_id>/download")
def download(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    storage_url = get_storage_url(pdf)
    if is_remote_storage_reference(storage_url):
        return redirect(storage_url)
    return redirect(storage_url or url_for("pdfs.list_pdfs"))


@bp.route("/<int:pdf_id>/delete", methods=["POST"])
@login_required
def delete(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    if pdf.uploaded_by != current_user.id and not current_user.is_admin:
        abort(403)

    if getattr(pdf, "public_id", None):
        delete_cloudinary_asset(pdf.public_id)

    db.session.delete(pdf)
    db.session.commit()
    flash("PDF deleted.", "info")
    return redirect(url_for("pdfs.list_pdfs"))
