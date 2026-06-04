import re
import json
import os
import shutil
from datetime import date

def main():
    # 1. Read version from rbwr_overlay.py
    with open("rbwr_overlay.py", "r", encoding="utf-8") as f:
        content = f.read()

    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        print("[ERROR] Could not find __version__ in rbwr_overlay.py!")
        exit(1)

    version = version_match.group(1)
    print(f"[INFO] Detected version: {version}")

    # 2. Update server/versions.json
    versions_json_path = os.path.join("server", "versions.json")
    if os.path.exists(versions_json_path):
        with open(versions_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"latest": "", "versions": {}}

    data["latest"] = version
    if version not in data["versions"]:
        # Add new version entry
        data["versions"][version] = {
            "version": version,
            "filename": f"rbwr_overlay_v{version}.exe",
            "release_date": str(date.today()),
            "notes": f"Release v{version} - auto-compiled and deployed."
        }
    else:
        # Update filename and release date just in case
        data["versions"][version]["filename"] = f"rbwr_overlay_v{version}.exe"
        data["versions"][version]["release_date"] = str(date.today())

    with open(versions_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"[INFO] Updated {versions_json_path} successfully.")

    # 3. Copy compiled executable to server/files/
    compiled_exe = "rbwr_overlay.exe"
    dest_dir = os.path.join("server", "files")
    dest_exe = os.path.join(dest_dir, f"rbwr_overlay_v{version}.exe")

    if os.path.exists(compiled_exe):
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(compiled_exe, dest_exe)
        print(f"[INFO] Copied {compiled_exe} to {dest_exe} successfully.")
    else:
        print(f"[WARN] Compiled executable {compiled_exe} not found in root directory. Copy skipped.")

if __name__ == "__main__":
    main()
