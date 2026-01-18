from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import sys
from pathlib import Path
import tempfile
import os
import json
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.auth.auth import create_user, authenticate_user, get_user_by_id
from app.project.project_manager import create_project, get_user_projects, get_project_by_id, delete_project
from app.core.gl_pipeline import GLPipeline
from app.core.mapping import MultiEntityProcessor
from app.utils.file_manager import save_uploaded_file
from app.excel.databook_generator import DatabookGenerator
from app.core.mapping import GLAccountMapper

app = FastAPI(
    title="QoE Tool API",
    description="Internal Quality of Experience Tool API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_id = int(token)
        # For frontend-only projects, allow any user_id without checking database
        try:
            user = get_user_by_id(user_id)
            if user:
                return user_id
        except:
            pass
        # Return the user_id even if not in database (for frontend-only projects)
        return user_id
    except (ValueError, TypeError):
        # Return default user ID for frontend-only projects
        return 1

class SignUpRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "QoE Tool API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/auth/signup")
async def signup(request: SignUpRequest):
    user = create_user(
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name
    )
    if not user:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    return {"message": "User created successfully", "user_id": user.id}

@app.post("/auth/login")
async def login(request: LoginRequest):
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = str(user.id)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name
        }
    }

@app.get("/projects")
async def list_projects(user_id: int = Depends(get_current_user_id)):
    projects = get_user_projects(user_id)
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "files": [{"id": f.id, "filename": f.filename} for f in (p.files or [])],
            "databooks": [{"id": d.id, "filename": d.filename} for d in (p.databooks or [])]
        }
        for p in projects
    ]

@app.post("/projects")
async def create_new_project(project: ProjectCreate, user_id: int = Depends(get_current_user_id)):
    new_project = create_project(user_id, project.title, project.description)
    if not new_project:
        raise HTTPException(status_code=400, detail="Failed to create project")
    return {
        "id": new_project.id,
        "title": new_project.title,
        "description": new_project.description,
        "created_at": new_project.created_at.isoformat() if new_project.created_at else None
    }

@app.get("/projects/{project_id}")
async def get_project(project_id: int, user_id: int = Depends(get_current_user_id)):
    project = get_project_by_id(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "files": [{"id": f.id, "filename": f.filename} for f in (project.files or [])],
        "databooks": [{"id": d.id, "filename": d.filename} for d in (project.databooks or [])]
    }

@app.delete("/projects/{project_id}")
async def delete_project_endpoint(project_id: int, user_id: int = Depends(get_current_user_id)):
    success = delete_project(project_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    return {"message": "Project deleted successfully"}

@app.options("/projects/{project_id}/process")
async def options_process():
    return {"message": "OK"}

@app.post("/projects/{project_id}/process")
async def process_gl_files(
    project_id: int,
    files: List[UploadFile] = File(...),
    source_system: str = Form(...),
    entity_configs: str = Form(...),
    user_id: int = Depends(get_current_user_id)
):
    # Note: Project validation is optional since projects are stored in frontend localStorage
    # We still accept the project_id for reference but don't require it to exist in DB
    try:
        project = get_project_by_id(project_id, user_id)
    except:
        project = None  # Allow processing even if project doesn't exist in DB
    
    try:
        try:
            configs = json.loads(entity_configs)
        except:
            configs = []
        
        if not isinstance(configs, list):
            configs = [configs] if configs else []
        
        entity_map = {}
        for c in configs:
            if isinstance(c, str):
                try:
                    c = json.loads(c)
                except:
                    continue
            if isinstance(c, dict) and "filename" in c and "entity_name" in c:
                entity_map[c["filename"]] = c["entity_name"]
        
        tmp_paths = []
        file_entity_pairs = []
        
        try:
            for uploaded_file in files:
                entity_name = entity_map.get(uploaded_file.filename, uploaded_file.filename)
                file_content = await uploaded_file.read()
                
                # Save file to temp directory (projects stored in frontend localStorage)
                try:
                    # Try to save via file manager (if project exists in DB)
                    project_file = save_uploaded_file(
                        project_id=project_id,
                        file_content=file_content,
                        filename=uploaded_file.filename,
                        entity_name=entity_name,
                        source_system=source_system
                    )
                    tmp_path = project_file.file_path
                except Exception as e:
                    # Fallback: save to temp file (for frontend-only projects)
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                    tmp_file.write(file_content)
                    tmp_file.close()
                    tmp_path = tmp_file.name
                
                tmp_paths.append(tmp_path)
                file_entity_pairs.append((tmp_path, entity_name))
            
            if len(file_entity_pairs) == 1:
                pipeline = GLPipeline()
                normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                    file_path=file_entity_pairs[0][0],
                    entity=file_entity_pairs[0][1],
                    source_system=source_system
                )
            else:
                processor = MultiEntityProcessor()
                normalized_df, processing_reports, validation_result = processor.process_multiple_files(
                    file_entity_pairs=file_entity_pairs,
                    source_system=source_system
                )
                processing_report = processing_reports[0] if processing_reports else None
            
            excel_file_url = None
            if validation_result.is_valid():
                try:
                    entity_info = None
                    if "entity" in normalized_df.columns:
                        entities = normalized_df["entity"].unique()
                        if len(entities) == 1:
                            entity_info = entities[0]
                    
                    mapper = GLAccountMapper()
                    auto_mapping_df = mapper.generate_auto_mapping_df(normalized_df, entity=entity_info)
                    
                    # Ensure output directory exists
                    output_dir = Path("output")
                    output_dir.mkdir(exist_ok=True)
                    
                    default_filename = f"GL_Databook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    output_path = output_dir / default_filename
                    
                    generator = DatabookGenerator(break_formulas=False)
                    
                    output_path = generator.generate_databook(
                        output_path=str(output_path),
                        normalized_df=normalized_df,
                        validation_result=validation_result,
                        processing_report=processing_report,
                        source_files=[f.filename for f in files],
                        entity=entity_info,
                        mapping_df=auto_mapping_df
                    )
                    
                    excel_file_url = f"/projects/{project_id}/download/{os.path.basename(output_path)}"
                except Exception as e:
                    print(f"Error generating Excel: {e}")
            
            return {
                "validation_result": {
                    "is_valid": validation_result.is_valid(),
                    "key_metrics": validation_result.key_metrics or {},
                    "errors": validation_result.errors or [],
                    "warnings": validation_result.warnings or []
                },
                "processed_data": normalized_df.to_dict(orient="records")[:1000],
                "excel_file_url": excel_file_url
            }
        finally:
            for tmp_path in tmp_paths:
                if os.path.exists(tmp_path) and tmp_path.startswith(tempfile.gettempdir()):
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()  # Print full traceback to console for debugging
        raise HTTPException(status_code=500, detail=f"Processing error: {error_detail}")

@app.get("/projects/{project_id}/download/{filename}")
async def download_file(project_id: int, filename: str, user_id: int = Depends(get_current_user_id)):
    try:
        project = get_project_by_id(project_id, user_id)
    except:
        project = None
    
    file_path = os.path.join("output", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )
