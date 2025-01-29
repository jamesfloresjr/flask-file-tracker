from flask import Blueprint, render_template
from .models import File  # Import your SQLAlchemy model

views = Blueprint('views', __name__)

@views.route('/')
def index():
    # Get the most recent 100 files
    recent_files = File.query.order_by(File.id.desc()).limit(100).all()

    # Categorize the files based on their status
    in_progress_files = [file for file in recent_files if file.status == File.IN_PROGRESS]
    completed_files = [file for file in recent_files if file.status == File.COMPLETED]
    failed_files = [file for file in recent_files if file.status == File.FAILED]

    # Pass the categorized files into the context for the template
    context = {
        'in_progress': in_progress_files,
        'completed': completed_files,
        'failed': failed_files,
    }

    return render_template("index.html", **context)
