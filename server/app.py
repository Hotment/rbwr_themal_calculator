from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import os
import json
from datetime import datetime, timezone, timedelta

app = FastAPI(
    title="RBWR APR Overlay Server",
    description="Provides update checks and a Feedback & Suggestions platform with IP ban tools.",
    version="1.5.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
VERSIONS_FILE = os.path.join(BASE_DIR, "versions.json")
SUGGESTIONS_FILE = os.path.join(BASE_DIR, "suggestions.json")
BANNED_FILE = os.path.join(BASE_DIR, "banned_ips.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Ensure files directory exists
os.makedirs(FILES_DIR, exist_ok=True)

def load_env():
    # Load environment variables from .env file if it exists
    path = ENV_FILE
    if not os.path.exists(path) and os.path.exists(".env"):
        path = ".env"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                            v = v[1:-1]
                        os.environ[k] = v
        except Exception:
            pass

load_env()

# --- Authentication & Persistence Helpers ---

security_basic = HTTPBasic()

def get_admin_credentials():
    return os.environ.get("ADMIN_USERNAME", "admin"), os.environ.get("ADMIN_PASSWORD", "adminpassword")

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security_basic)):
    correct_user, correct_pass = get_admin_credentials()
    if credentials.username != correct_user or credentials.password != correct_pass:
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
    name: str
    suggestion: str
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
    
    # Enforce rate limiting: 1 feedback entry per 12 hours per IP (bypassed for local development)
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
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APRM Overlay Admin - Feedback & Suggestions Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #07080a; font-family: 'Consolas', 'Segoe UI', monospace; color: #ffffff; }
        .cyber-panel { background-color: #11141a; border: 1px solid #1a202c; }
        .glow-cyan { border-color: #00f0ff; box-shadow: 0 0 10px rgba(0, 240, 255, 0.25); }
        .accent-cyan { color: #00f0ff; }
        .accent-green { color: #39ff14; }
        .accent-red { color: #ff003c; }
        .accent-gold { color: #ffaa00; }
        .btn-accent { border: 1px solid #00f0ff; color: #00f0ff; background-color: transparent; transition: all 0.2s; }
        .btn-accent:hover { background-color: #00f0ff; color: #07080a; }
    </style>
</head>
<body class="p-6 md:p-10">
    <div class="max-w-6xl mx-auto">
        <!-- Header -->
        <header class="cyber-panel glow-cyan p-6 rounded mb-8 flex flex-col md:flex-row justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold tracking-widest accent-cyan">[ // FEEDBACK & SUGGESTIONS CONTROL CENTER ]</h1>
                <p class="text-xs text-slate-500 mt-1">Logged in as __USERNAME__ // Terminal session active</p>
            </div>
            <div class="mt-4 md:mt-0 flex gap-4 text-xs font-bold text-slate-400">
                <div>ACTIVE BANS: <span id="stat-active-bans" class="accent-red">0</span></div>
                <div>TOTAL ENTRIES: <span id="stat-total-entries" class="accent-cyan">0</span></div>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
            <!-- Sidebar / Active Bans -->
            <div class="lg:col-span-1 flex flex-col gap-6">
                <div class="cyber-panel p-5 rounded border border-slate-800">
                    <h2 class="text-sm font-bold tracking-wider accent-gold mb-4">[ BANNED IP INDEX ]</h2>
                    <div id="banned-ips-container" class="flex flex-col gap-3 max-h-[400px] overflow-y-auto pr-1">
                        <p class="text-xs text-slate-500 italic">Loading bans...</p>
                    </div>
                </div>
            </div>

            <!-- Main Feedback & Suggestions Feed -->
            <div class="lg:col-span-3 flex flex-col gap-6">
                <!-- Filter Tabs -->
                <div class="flex border-b border-slate-800 gap-2 text-xs font-bold">
                    <button onclick="filterStatus('all')" id="tab-all" class="px-4 py-2 text-white border-b-2 border-[#00f0ff] uppercase">All</button>
                    <button onclick="filterStatus('pending')" id="tab-pending" class="px-4 py-2 text-slate-400 hover:text-white uppercase">Pending</button>
                    <button onclick="filterStatus('considering')" id="tab-considering" class="px-4 py-2 text-slate-400 hover:text-white uppercase">Considering</button>
                    <button onclick="filterStatus('accepted')" id="tab-accepted" class="px-4 py-2 text-slate-400 hover:text-white uppercase">Accepted</button>
                    <button onclick="filterStatus('declined')" id="tab-declined" class="px-4 py-2 text-slate-400 hover:text-white uppercase">Declined</button>
                </div>

                <!-- Feed Entries -->
                <div id="feed-container" class="flex flex-col gap-4">
                    <p class="text-sm text-slate-500 italic">Loading suggestions...</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Ban Overlay Modal -->
    <div id="ban-modal" class="fixed inset-0 bg-black/85 backdrop-blur-sm hidden flex items-center justify-center p-4">
        <div class="cyber-panel glow-cyan p-6 rounded max-w-sm w-full flex flex-col gap-4">
            <h3 class="text-sm font-bold tracking-widest accent-red">[ // ENFORCE IP BAN PROTOCOL ]</h3>
            <div class="flex flex-col gap-1 text-xs">
                <label class="text-slate-500">TARGET IP ADDRESS</label>
                <input type="text" id="ban-ip-field" readonly class="bg-[#0b0d12] border border-slate-800 p-2 rounded text-slate-300 outline-none">
            </div>
            <div class="flex flex-col gap-1 text-xs">
                <label class="text-slate-500">BAN EXPIRATION / DURATION</label>
                <select id="ban-duration" class="bg-[#0b0d12] border border-slate-800 p-2 rounded text-slate-300 outline-none">
                    <option value="60">1 Hour</option>
                    <option value="1440">24 Hours</option>
                    <option value="10080">7 Days</option>
                    <option value="permanent">Permanent</option>
                </select>
            </div>
            <div class="flex flex-col gap-1 text-xs">
                <label class="text-slate-500">REASON FOR PROHIBITION</label>
                <input type="text" id="ban-reason" placeholder="e.g. Spammed submission logs" class="bg-[#0b0d12] border border-slate-800 p-2 rounded text-slate-300 outline-none">
            </div>
            <div class="flex gap-3 justify-end text-xs font-bold mt-2">
                <button onclick="closeBanModal()" class="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded uppercase">Cancel</button>
                <button onclick="submitBan()" class="px-4 py-2 bg-red-950 text-red-500 hover:bg-red-900 hover:text-white rounded uppercase">Enforce Ban</button>
            </div>
        </div>
    </div>

    <!-- JS Dashboard Logic -->
    <script>
        let currentFilter = 'all';
        let bannedIps = {};

        function filterStatus(status) {
            currentFilter = status;
            const tabs = document.querySelectorAll('button[id^="tab-"]');
            tabs.forEach(tab => {
                tab.classList.remove('border-b-2', 'border-[#00f0ff]', 'text-white');
                tab.classList.add('text-slate-400');
            });
            document.getElementById('tab-' + status).classList.add('border-b-2', 'border-[#00f0ff]', 'text-white');
            document.getElementById('tab-' + status).classList.remove('text-slate-400');
            
            applyFilter();
        }

        function applyFilter() {
            const cards = document.querySelectorAll('.suggestion-card');
            cards.forEach(card => {
                if (currentFilter === 'all' || card.getAttribute('data-status') === currentFilter) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        async function fetchDashboardData() {
            try {
                const response = await fetch('/admin/suggestions/data');
                if (response.ok) {
                    const data = await response.json();
                    bannedIps = data.banned_ips;
                    updateStats(data);
                    renderBannedIps(data.banned_ips);
                    renderSuggestions(data.suggestions);
                }
            } catch (err) {
                console.error('Error fetching dashboard data:', err);
            }
        }

        function updateStats(data) {
            const activeBans = Object.keys(data.banned_ips).length;
            const totalEntries = data.suggestions.length;
            document.getElementById('stat-active-bans').innerText = activeBans;
            document.getElementById('stat-total-entries').innerText = totalEntries;
        }

        function renderBannedIps(bans) {
            const container = document.getElementById('banned-ips-container');
            const ipList = Object.keys(bans);
            if (ipList.length === 0) {
                container.innerHTML = '<p class="text-xs text-slate-500 italic">No IPs currently banned.</p>';
                return;
            }
            
            let html = '';
            for (const ip of ipList) {
                const info = bans[ip];
                const expires = info.expires_at ? info.expires_at.replace('T', ' ').substring(0, 16) : "Permanent";
                html += `
                    <div class="bg-[#0b0d12] p-3 rounded border border-red-950 text-xs">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-bold text-red-500">${ip}</span>
                            <button onclick="unbanIP('${ip}')" class="text-slate-400 hover:text-white underline">Unban</button>
                        </div>
                        <div class="text-slate-500 mt-1 break-words">Reason: ${escapeHtml(info.reason || "N/A")}</div>
                        <div class="text-[10px] text-slate-600 mt-1">Expires: ${expires}</div>
                    </div>
                `;
            }
            container.innerHTML = html;
        }

        function renderSuggestions(suggestions) {
            const container = document.getElementById('feed-container');
            if (suggestions.length === 0) {
                container.innerHTML = '<p class="text-sm text-slate-500 italic">No feedback or suggestions submitted yet.</p>';
                return;
            }

            let html = '';
            for (const s of suggestions) {
                const timeStr = (s.timestamp || '').substring(0, 19).replace('T', ' ');
                const isBanned = s.ip in bannedIps;
                
                let badgeClass = '';
                if (s.status === 'pending') badgeClass = 'bg-amber-950 text-amber-400';
                else if (s.status === 'considering') badgeClass = 'bg-blue-950 text-blue-400';
                else if (s.status === 'accepted') badgeClass = 'bg-emerald-950 text-emerald-400';
                else if (s.status === 'declined') badgeClass = 'bg-rose-950 text-rose-400';

                const banBtn = isBanned 
                    ? `<button onclick="unbanIP('${s.ip}')" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded font-bold uppercase">Unban IP</button>`
                    : `<button onclick="openBanModal('${s.ip}')" class="px-3 py-1 bg-red-950/40 hover:bg-red-950 text-red-500 text-xs rounded font-bold uppercase">Ban IP</button>`;

                const bannedTag = isBanned 
                    ? '<span class="px-1.5 py-0.2 bg-red-950 text-red-500 text-[9px] rounded font-bold uppercase">Banned</span>'
                    : '';

                html += `
                    <div class="suggestion-card cyber-panel p-5 rounded border border-slate-800 flex flex-col gap-3" data-status="${s.status || 'pending'}">
                        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                            <div class="flex items-center gap-3">
                                <span class="text-sm font-bold text-slate-200">${escapeHtml(s.name || 'Anonymous')}</span>
                                <span class="text-[10px] text-slate-500">${timeStr}</span>
                                <span class="px-2 py-0.5 rounded text-[10px] uppercase font-bold ${badgeClass}">${s.status}</span>
                            </div>
                            <div class="text-[11px] text-slate-400 flex items-center gap-2">
                                <span>Sender IP: <span class="font-mono text-slate-300">${s.ip}</span></span>
                                ${bannedTag}
                            </div>
                        </div>
                        <p class="text-sm text-slate-300 bg-[#0b0d12] p-4 rounded border border-slate-900 leading-relaxed font-mono whitespace-pre-wrap">${escapeHtml(s.suggestion)}</p>
                        
                        <!-- Action Controls -->
                        <div class="flex flex-wrap justify-between items-center gap-4 mt-1 border-t border-slate-900 pt-3">
                            <div class="flex gap-2">
                                <button onclick="updateStatus(${s.id}, 'accepted')" class="px-3 py-1 bg-emerald-950 hover:bg-emerald-900 text-emerald-400 text-xs rounded font-bold uppercase">Accept</button>
                                <button onclick="updateStatus(${s.id}, 'considering')" class="px-3 py-1 bg-blue-950 hover:bg-blue-900 text-blue-400 text-xs rounded font-bold uppercase">Consider</button>
                                <button onclick="updateStatus(${s.id}, 'declined')" class="px-3 py-1 bg-rose-950 hover:bg-rose-900 text-rose-400 text-xs rounded font-bold uppercase">Decline</button>
                                <button onclick="updateStatus(${s.id}, 'pending')" class="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-slate-400 text-xs rounded font-bold uppercase">Pending</button>
                            </div>
                            <div>
                                ${banBtn}
                            </div>
                        </div>
                    </div>
                `;
            }
            container.innerHTML = html;
            applyFilter();
        }

        function escapeHtml(text) {
            if (!text) return '';
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, function(m) { return map[m]; });
        }

        async function updateStatus(id, status) {
            try {
                const response = await fetch('/admin/suggestions/status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id, status })
                });
                if (response.ok) {
                    await fetchDashboardData();
                } else {
                    alert('Failed to update status.');
                }
            } catch (err) {
                alert('Network error updating status.');
            }
        }

        async function unbanIP(ip) {
            try {
                const response = await fetch('/admin/suggestions/unban', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip })
                });
                if (response.ok) {
                    await fetchDashboardData();
                } else {
                    alert('Failed to unban IP.');
                }
            } catch (err) {
                alert('Network error unbanning IP.');
            }
        }

        function openBanModal(ip) {
            document.getElementById('ban-ip-field').value = ip;
            document.getElementById('ban-modal').classList.remove('hidden');
        }

        function closeBanModal() {
            document.getElementById('ban-modal').classList.add('hidden');
        }

        async function submitBan() {
            const ip = document.getElementById('ban-ip-field').value;
            const durationVal = document.getElementById('ban-duration').value;
            const reason = document.getElementById('ban-reason').value;
            
            const duration_minutes = durationVal === 'permanent' ? null : parseInt(durationVal);
            
            try {
                const response = await fetch('/admin/suggestions/ban', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip, duration_minutes, reason })
                });
                if (response.ok) {
                    closeBanModal();
                    document.getElementById('ban-reason').value = '';
                    await fetchDashboardData();
                } else {
                    alert('Failed to ban IP.');
                }
            } catch (err) {
                alert('Network error performing IP ban.');
            }
        }

        // Initial load
        fetchDashboardData();
        // Poll every 5 seconds
        setInterval(fetchDashboardData, 5000);
    </script>
</body>
</html>""".replace("__USERNAME__", username)
    return HTMLResponse(content=html_content, status_code=200)
