from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
import json

app = FastAPI(
    title="RBWR APR Overlay Version Control Server",
    description="Provides API endpoints to query latest version and download script releases.",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
VERSIONS_FILE = os.path.join(BASE_DIR, "versions.json")

# Ensure files directory exists
os.makedirs(FILES_DIR, exist_ok=True)

def load_versions():
    if not os.path.exists(VERSIONS_FILE):
        default_data = {
            "latest": "1.2.0",
            "versions": {
                "1.2.0": {
                    "version": "1.2.0",
                    "filename": "rbwr_overlay.py",
                    "release_date": "2026-06-01",
                    "notes": "Added HUD toggle, OCR speed optimizations, persistent variables, and right-click context menus."
                }
            }
        }
        with open(VERSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(VERSIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "RBWR APR Overlay Version Control Server is running.",
        "endpoints": {
            "latest_version": "/version/latest",
            "all_versions": "/versions",
            "download_latest": "/download/latest",
            "download_specific": "/download/{version}"
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
    
    # Fallback to parent directory if not placed in files/ yet
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
