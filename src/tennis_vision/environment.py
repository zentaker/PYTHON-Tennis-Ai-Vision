"""Local environment checks for Tennis AI Vision."""

from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FOLDERS = (
    "samples",
    "src",
    "src/tennis_vision",
    "scripts",
    "outputs",
    "outputs/reports",
    "outputs/logs",
    "outputs/frames",
    "outputs/annotated",
)

REQUIRED_PACKAGES = {
    "opencv-python": "cv2",
    "numpy": "numpy",
    "pandas": "pandas",
    "pydantic": "pydantic",
    "rich": "rich",
}


def check_python_version() -> dict[str, Any]:
    """Return details about the active Python runtime."""
    version_info = sys.version_info
    return {
        "version": platform.python_version(),
        "executable": sys.executable,
        "major": version_info.major,
        "minor": version_info.minor,
        "micro": version_info.micro,
        "supported": version_info >= (3, 10),
    }


def check_current_working_directory() -> dict[str, str]:
    """Return the current working directory."""
    return {"path": str(Path.cwd())}


def check_operating_system() -> dict[str, str]:
    """Return operating system details."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "platform": platform.platform(),
    }


def check_required_folders(project_root: Path) -> dict[str, dict[str, Any]]:
    """Check whether required project folders exist."""
    status: dict[str, dict[str, Any]] = {}
    for folder in REQUIRED_FOLDERS:
        path = project_root / folder
        status[folder] = {
            "exists": path.exists() and path.is_dir(),
            "path": str(path),
        }
    return status


def check_required_packages() -> dict[str, dict[str, Any]]:
    """Check whether required packages can be imported."""
    status: dict[str, dict[str, Any]] = {}
    for package_name, import_name in REQUIRED_PACKAGES.items():
        spec = importlib.util.find_spec(import_name)
        import_error = None
        available = spec is not None
        if spec is not None:
            try:
                importlib.import_module(import_name)
            except Exception as exc:  # Some imports can fail because of native DLL issues.
                available = False
                import_error = str(exc)
        status[package_name] = {
            "import_name": import_name,
            "available": available,
            "origin": getattr(spec, "origin", None) if spec else None,
            "error": import_error,
        }
    return status


def check_ffmpeg() -> dict[str, Any]:
    """Check whether ffmpeg is available from the shell."""
    executable = shutil.which("ffmpeg")
    result: dict[str, Any] = {
        "available": executable is not None,
        "path": executable,
        "version": None,
        "error": None,
    }

    if executable is None:
        result["error"] = "ffmpeg command was not found in PATH."
        return result

    try:
        completed = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
        result["version"] = first_line
        if completed.returncode != 0:
            result["available"] = False
            result["error"] = completed.stderr.strip() or "ffmpeg returned a non-zero exit code."
    except (OSError, subprocess.SubprocessError) as exc:
        result["available"] = False
        result["error"] = str(exc)

    return result


def check_samples_folder(project_root: Path) -> dict[str, Any]:
    """Check the samples folder specifically for Stage 0 reporting."""
    path = project_root / "samples"
    return {
        "exists": path.exists() and path.is_dir(),
        "path": str(path),
    }


def check_reports_folder(project_root: Path) -> dict[str, Any]:
    """Check the reports folder specifically for Stage 0 reporting."""
    path = project_root / "outputs" / "reports"
    return {
        "exists": path.exists() and path.is_dir(),
        "path": str(path),
    }


def run_environment_checks(project_root: Path | None = None) -> dict[str, Any]:
    """Run all Stage 0 environment checks."""
    root = project_root or Path.cwd()
    folder_status = check_required_folders(root)
    package_status = check_required_packages()
    ffmpeg_status = check_ffmpeg()

    errors: list[str] = []
    warnings: list[str] = []
    recommended_fixes: list[str] = []

    missing_folders = [
        folder for folder, details in folder_status.items() if not details["exists"]
    ]
    missing_packages = [
        package for package, details in package_status.items() if not details["available"]
    ]

    if missing_folders:
        errors.append(f"Missing required folders: {', '.join(missing_folders)}")
        recommended_fixes.append("Recreate the missing folders from the repository structure.")

    if missing_packages:
        errors.append(f"Missing required packages: {', '.join(missing_packages)}")
        recommended_fixes.append("Run: python -m pip install -r requirements.txt")

    if not ffmpeg_status["available"]:
        warnings.append("ffmpeg is not available from the terminal.")
        recommended_fixes.append(
            "Install ffmpeg locally and confirm that `ffmpeg -version` works in a new terminal."
        )

    python_status = check_python_version()
    if not python_status["supported"]:
        warnings.append("Python 3.10 or newer is recommended for future stages.")
        recommended_fixes.append("Install and activate Python 3.10 or newer.")

    return {
        "project_root": str(root),
        "cwd": check_current_working_directory(),
        "os": check_operating_system(),
        "python": python_status,
        "packages": package_status,
        "folders": folder_status,
        "ffmpeg": ffmpeg_status,
        "samples": check_samples_folder(root),
        "reports_folder": check_reports_folder(root),
        "missing_packages": missing_packages,
        "missing_folders": missing_folders,
        "errors": errors,
        "warnings": warnings,
        "recommended_fixes": recommended_fixes,
    }
