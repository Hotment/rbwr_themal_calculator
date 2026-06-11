from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
import os
import json
import secrets
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

app = FastAPI(
    title="RBWR APR Overlay Server",
    description="Provides update checks and a Feedback & Suggestions platform with IP ban tools.",
    version="1.5.1"
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
VERSIONS_FILE = os.path.join(BASE_DIR, "versions.json")
SUGGESTIONS_FILE = os.path.join(BASE_DIR, "suggestions.json")
BANNED_FILE = os.path.join(BASE_DIR, "banned_ips.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Ensure files directory exists
os.makedirs(FILES_DIR, exist_ok=True)

load_dotenv()

# --- Authentication & Persistence Helpers ---
security_basic = HTTPBasic()

_generated_admin_user = secrets.token_hex(12)
_generated_admin_pass = secrets.token_hex(24)

if not os.environ.get("ADMIN_USERNAME") or not os.environ.get("ADMIN_PASSWORD"):
    import logging
    logging.getLogger("uvicorn.error").warning(
        "[SECURITY] ADMIN_USERNAME or ADMIN_PASSWORD is not set in the environment/dotenv. "
        "A random secure credential has been dynamically generated for this server session."
    )

def get_admin_credentials():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    return username or _generated_admin_user, password or _generated_admin_pass

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security_basic)):
    correct_user, correct_pass = get_admin_credentials()
    is_correct_username = secrets.compare_digest(credentials.username, correct_user)
    is_correct_password = secrets.compare_digest(credentials.password, correct_pass)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def load_versions():
    if not os.path.exists(VERSIONS_FILE):
        default_data = {
            "latest": "1.4.1",
            "versions": {
                "1.4.1": {
                    "version": "1.4.1",
                    "filename": "rbwr_overlay_v1.4.1.exe",
                    "release_date": "2026-06-04",
                    "notes": "Dynamic facility usage integration and UI enhancements."
                }
            }
        }
        with open(VERSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(VERSIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_suggestions():
    if not os.path.exists(SUGGESTIONS_FILE):
        return {"suggestions": []}
    with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"suggestions": []}

def save_suggestions(data):
    with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_banned_ips():
    if not os.path.exists(BANNED_FILE):
        return {"banned": {}}
    with open(BANNED_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"banned": {}}

def save_banned_ips(data):
    with open(BANNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def is_ip_banned(ip: str) -> bool:
    if ip == "unknown":
        return False
    data = load_banned_ips()
    banned = data.get("banned", {})
    if ip not in banned:
        return False
    
    ban_info = banned[ip]
    expires_at_str = ban_info.get("expires_at")
    if expires_at_str is None:
        # Permanent ban
        return True
    
    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now(timezone.utc) > expires_at:
            # Ban expired, remove record
            del banned[ip]
            save_banned_ips(data)
            return False
        return True
    except Exception:
        return True

# --- API Endpoints ---

class SuggestionPayload(BaseModel):
    name: str = Field(default="", max_length=50)
    suggestion: str = Field(..., max_length=2000)
    anonymous: bool

class StatusUpdatePayload(BaseModel):
    id: int
    status: str

class BanPayload(BaseModel):
    ip: str
    duration_minutes: int | None = None  # None for permanent
    reason: str

class UnbanPayload(BaseModel):
    ip: str


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "RBWR APR Overlay Server is running.",
        "endpoints": {
            "latest_version": "/version/latest",
            "all_versions": "/versions",
            "download_latest": "/download/latest",
            "submit_suggestion": "POST /suggestions",
            "admin_suggestions": "GET /admin/suggestions"
        }
    }

@app.get("/version/latest", tags=["Metadata"])
def get_latest_version():
    data = load_versions()
    latest_ver = data.get("latest")
    latest_meta = data.get("versions", {}).get(latest_ver)
    if not latest_meta:
        raise HTTPException(status_code=404, detail="Latest version metadata not found")
    return latest_meta

@app.get("/versions", tags=["Metadata"])
def get_all_versions():
    data = load_versions()
    return data.get("versions", {})

@app.get("/download/latest", tags=["Downloads"])
def download_latest_file():
    data = load_versions()
    latest_ver = data.get("latest")
    latest_meta = data.get("versions", {}).get(latest_ver)
    if not latest_meta:
        raise HTTPException(status_code=404, detail="Latest version metadata not found")
    
    filename = latest_meta.get("filename")
    filepath = os.path.join(FILES_DIR, filename)
    
    if not os.path.exists(filepath):
        parent_filepath = os.path.join(os.path.dirname(BASE_DIR), filename)
        if os.path.exists(parent_filepath):
            return FileResponse(parent_filepath, media_type="application/octet-stream", filename=filename)
        raise HTTPException(status_code=404, detail=f"Latest release file '{filename}' is missing on the server.")
        
    return FileResponse(filepath, media_type="application/octet-stream", filename=filename)

@app.get("/download/{version}", tags=["Downloads"])
def download_version_file(version: str):
    data = load_versions()
    version_meta = data.get("versions", {}).get(version)
    if not version_meta:
        raise HTTPException(status_code=404, detail=f"Version '{version}' not found in the catalog.")
    
    filename = version_meta.get("filename")
    filepath = os.path.join(FILES_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File for version '{version}' is missing on the server.")
        
    return FileResponse(filepath, media_type="application/octet-stream", filename=filename)


@app.post("/suggestions", tags=["Feedback & Suggestions"])
def submit_suggestion(payload: SuggestionPayload, request: Request):
    ip = request.client.host if request.client else "unknown"
    if is_ip_banned(ip):
        raise HTTPException(status_code=403, detail="Your IP is banned from submitting feedback.")
    
    if not payload.suggestion.strip():
        raise HTTPException(status_code=400, detail="Feedback details cannot be empty.")
    
    data = load_suggestions()
    suggestions = data.setdefault("suggestions", [])
    
    # Enforce rate limiting: 1 feedback entry per 12 hours per IP
    if ip != "unknown":
        now = datetime.now(timezone.utc)
        limit_period = timedelta(hours=12)
        for s in suggestions:
            if s.get("ip") == ip:
                try:
                    s_time = datetime.fromisoformat(s.get("timestamp"))
                    if now - s_time < limit_period:
                        time_left = limit_period - (now - s_time)
                        hours_left = int(time_left.total_seconds() // 3600)
                        mins_left = int((time_left.total_seconds() % 3600) // 60)
                        msg = f"Rate limit: Try again in {hours_left}h {mins_left}m."
                        raise HTTPException(status_code=429, detail=msg)
                except (ValueError, TypeError):
                    continue
    
    new_id = 1
    if suggestions:
        new_id = max(s.get("id", 0) for s in suggestions) + 1
        
    name = "Anonymous" if payload.anonymous or not payload.name.strip() else payload.name.strip()
    
    new_sug = {
        "id": new_id,
        "name": name,
        "suggestion": payload.suggestion.strip(),
        "ip": ip,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pending"
    }
    suggestions.append(new_sug)
    save_suggestions(data)
    return {"message": "Feedback submitted successfully.", "id": new_id}


# --- Admin API / Dashboard ---

@app.post("/admin/suggestions/status", tags=["Admin Feedback & Suggestions API"])
def update_suggestion_status(payload: StatusUpdatePayload, username: str = Depends(authenticate_admin)):
    data = load_suggestions()
    suggestions = data.get("suggestions", [])
    for s in suggestions:
        if s.get("id") == payload.id:
            s["status"] = payload.status
            save_suggestions(data)
            return {"message": "Status updated successfully.", "id": payload.id, "status": payload.status}
    raise HTTPException(status_code=404, detail=f"Feedback/suggestion with ID {payload.id} not found.")

@app.post("/admin/suggestions/ban", tags=["Admin Feedback & Suggestions API"])
def ban_ip(payload: BanPayload, username: str = Depends(authenticate_admin)):
    data = load_banned_ips()
    banned = data.setdefault("banned", {})
    
    expires_at = None
    if payload.duration_minutes is not None:
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes)).isoformat()
        
    banned[payload.ip] = {
        "banned_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "reason": payload.reason.strip() or "No reason provided"
    }
    save_banned_ips(data)
    return {"message": f"IP {payload.ip} banned successfully.", "ip": payload.ip}

@app.post("/admin/suggestions/unban", tags=["Admin Feedback & Suggestions API"])
def unban_ip(payload: UnbanPayload, username: str = Depends(authenticate_admin)):
    data = load_banned_ips()
    banned = data.get("banned", {})
    if payload.ip in banned:
        del banned[payload.ip]
        save_banned_ips(data)
        return {"message": f"IP {payload.ip} unbanned successfully.", "ip": payload.ip}
    raise HTTPException(status_code=404, detail=f"IP {payload.ip} is not currently banned.")


@app.get("/admin/suggestions/data", tags=["Admin Feedback & Suggestions API"])
def get_suggestions_data(username: str = Depends(authenticate_admin)):
    sug_data = load_suggestions()
    suggestions = sug_data.get("suggestions", [])
    suggestions = sorted(suggestions, key=lambda s: s.get("timestamp", ""), reverse=True)
    
    ban_data = load_banned_ips()
    banned_ips = ban_data.get("banned", {})
    
    return {
        "suggestions": suggestions,
        "banned_ips": banned_ips
    }


@app.get("/admin/suggestions", response_class=HTMLResponse, tags=["Admin Feedback & Suggestions Dashboard"])
def view_suggestions_dashboard(username: str = Depends(authenticate_admin)):
    template_path = os.path.join(TEMPLATES_DIR, "suggestions_dashboard.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template suggestions_dashboard.html not found.")
    
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    html_content = html_content.replace("__USERNAME__", username)
    return HTMLResponse(content=html_content, status_code=200)
