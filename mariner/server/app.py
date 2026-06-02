import os
from pathlib import Path
from typing import Sequence

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from whitenoise import WhiteNoise

from mariner import config


def get_frontend_assets_path() -> str:
    potential_paths: Sequence[Path] = [
        Path("./frontend/dist/"),
        Path("/opt/venvs/mariner3d/dist/"),
    ]
    try:
        path = next(path for path in potential_paths if path.exists() and path.is_dir())
    except StopIteration:
        # fallback to potential_paths. we're likely running from tests
        path = potential_paths[0]
    return str(path.absolute())


frontend_dist_directory: str = get_frontend_assets_path()
app: Flask = Flask(
    __name__,
    template_folder=frontend_dist_directory,
    static_folder=frontend_dist_directory,
)
csrf = CSRFProtect(app)
# pyre-ignore[8]: incompatible attribute type
app.wsgi_app = WhiteNoise(app.wsgi_app)
# pyre-ignore[16]: undefined attribute
app.wsgi_app.add_files(frontend_dist_directory)

app.config.from_mapping(
    {
        "DEBUG": True,
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": config.get_cache_directory(),
        "CACHE_DEFAULT_TIMEOUT": 300,
        "SECRET_KEY": os.urandom(16),
    }
)

import subprocess
from flask import send_file
import io

@app.route('/api/cam')
def live_camera_stream():
    """
    Schießt ein Turbo-Snapshot NUR, wenn das Dashboard die URL aufruft.
    Nutzt shell=True, damit Bookworm die Hardware-Treiber im RAM-Stream lädt.
    """
    try:
        cmd = "/usr/bin/rpicam-still -t 1 --immediate --width 640 --height 480 -q 80 -e jpg -o - --nopreview"
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=3)

        if result.returncode == 0 and result.stdout:
            return send_file(io.BytesIO(result.stdout), mimetype='image/jpeg')
    except Exception:
        pass

    # Fallback bei Hardware-Timeout
    return b'', 204

# Erlaubt dem Frontend, die Kamera-Last auf dem Pi komplett abzuschalten@app.route('/api/camera/<action>', methods=['POST'])
@csrf.exempt
def control_camera(action: str):
    if action == 'stop':
        import subprocess
        subprocess.run(["sudo", "systemctl", "stop", "mediamtx"])
        return {"status": "Kamera gestoppt, CPU entlastet"}, 200
    elif action == 'start':
        import subprocess
        subprocess.run(["sudo", "systemctl", "start", "mediamtx"])
        return {"status": "Kamera gestartet"}, 200
    return {"error": "Ungueltige Aktion"}, 400
