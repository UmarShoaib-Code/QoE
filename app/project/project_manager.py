"""
Project management functions
"""
from typing import Optional, List
from app.database.models import Project, get_session
from datetime import datetime


def create_project(user_id: int, title: str, description: Optional[str] = None) -> Optional[Project]:
    """Create a new project for a user"""
    db = get_session()
    try:
        new_project = Project(
            title=title,
            description=description,
            user_id=user_id
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        return new_project
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_user_projects(user_id: int) -> List[Project]:
    """Get all projects for a user"""
    db = get_session()
    try:
        return db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()
    finally:
        db.close()


def get_project_by_id(project_id: int, user_id: int) -> Optional[Project]:
    """Get a project by ID (ensures user owns it)"""
    db = get_session()
    try:
        return db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    finally:
        db.close()


def delete_project(project_id: int, user_id: int) -> bool:
    """Delete a project (ensures user owns it)"""
    db = get_session()
    try:
        project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

