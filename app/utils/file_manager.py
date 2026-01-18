"""
File management utilities for storing uploaded files
"""
import os
from pathlib import Path
from typing import Optional
from app.database.models import ProjectFile, get_session
from datetime import datetime


def get_uploads_directory() -> Path:
    """Get the directory for storing uploaded files"""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    return uploads_dir


def save_uploaded_file(project_id: int, file_content: bytes, filename: str, 
                      entity_name: Optional[str] = None, source_system: Optional[str] = None) -> Optional[ProjectFile]:
    """Save an uploaded file and create a database record"""
    db = get_session()
    try:
        # Check if project exists in database first
        from app.database.models import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            # Project doesn't exist in DB (stored in frontend localStorage)
            # Just save to temp directory and return a mock object
            import tempfile
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp_file.write(file_content)
            tmp_file.close()
            
            # Create a simple object with file_path attribute
            class TempFile:
                def __init__(self, path):
                    self.file_path = path
            return TempFile(tmp_file.name)
        
        # Create project-specific directory
        uploads_dir = get_uploads_directory()
        project_dir = uploads_dir / f"project_{project_id}"
        project_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = project_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        file_size = len(file_content)
        
        # Create database record
        project_file = ProjectFile(
            project_id=project_id,
            filename=filename,
            file_path=str(file_path),
            file_size=file_size,
            entity_name=entity_name,
            source_system=source_system
        )
        
        db.add(project_file)
        db.commit()
        db.refresh(project_file)
        return project_file
    except Exception as e:
        db.rollback()
        # If DB operation fails, fall back to temp file
        import tempfile
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        tmp_file.write(file_content)
        tmp_file.close()
        
        class TempFile:
            def __init__(self, path):
                self.file_path = path
        return TempFile(tmp_file.name)
    finally:
        db.close()


def get_project_files(project_id: int) -> list:
    """Get all files for a project"""
    db = get_session()
    try:
        return db.query(ProjectFile).filter(ProjectFile.project_id == project_id).order_by(ProjectFile.uploaded_at.desc()).all()
    finally:
        db.close()

