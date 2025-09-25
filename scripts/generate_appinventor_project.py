#!/usr/bin/env python3
"""Package the MIT App Inventor project into an AIA archive.

This helper rewrites the small bits of metadata that are deterministic and then
zips the checked-in source tree under ``app_inventor/DigitalGardenController``.
The generated ``DigitalGardenController.aia`` can be imported directly into MIT
App Inventor.  Running the script repeatedly is safe.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
import zipfile

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "app_inventor" / "DigitalGardenController"
SRC_DIR = PROJECT_DIR / "src" / "appinventor" / "ai_digitalgarden" / "DigitalGardenController"
ASSETS_DIR = PROJECT_DIR / "assets"
YOUNG_DIR = PROJECT_DIR / "youngandroidproject"
AIA_PATH = PROJECT_DIR / "DigitalGardenController.aia"

REQUIRED_FILES = (
    SRC_DIR / "Screen1.scm",
    SRC_DIR / "Screen1.bky",
)

PROJECT_PROPERTIES = """main=appinventor.ai_digitalgarden.DigitalGardenController.Screen1
name=DigitalGardenController
assets=../assets
source=../src
build=../build
versioncode=1
versionname=1.0
useslocation=False
aname=DigitalGardenController
sizing=Responsive
showlistsasjson=True
actionbar=True
theme=AppTheme.Light.DarkActionBar
color.primary=&HFF2196F3
color.primary.dark=&HFF1565C0
color.accent=&HFFFFC107
"""


class ConflictError(RuntimeError):
    """Raised when Git reports unresolved merge conflicts."""


def ensure_required_files() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        missing_text = "\n".join(f"  - {item}" for item in missing)
        raise FileNotFoundError(
            "The MIT App Inventor sources are incomplete. Make sure the following files exist:\n"
            f"{missing_text}\n"
            "If they were deleted, restore them with `git checkout -- app_inventor`."
        )


def list_git_conflicts() -> list[Path]:
    """Return the set of files that Git still considers conflicted."""

    try:
        result = subprocess.run(
            ["git", "ls-files", "-u"],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Failed to query git for conflicts") from exc

    conflicts = set()
    for line in result.stdout.splitlines():
        # The format is: <mode> <hash> <stage>\t<path>
        try:
            _metadata, path_str = line.split("\t", 1)
        except ValueError:  # pragma: no cover - defensive
            continue
        conflicts.add(REPO_ROOT / path_str)

    return sorted(conflicts)


def ensure_no_conflicts() -> None:
    conflicts = [path for path in list_git_conflicts() if path != AIA_PATH]
    if conflicts:
        file_list = "\n".join(f"  - {path.relative_to(REPO_ROOT)}" for path in conflicts)
        raise ConflictError(
            "Resolve the Git merge conflicts below before packaging the MIT App Inventor project:\n"
            f"{file_list}\n"
            "Open each file, remove the `<<<<<<<`, `=======`, and `>>>>>>>` markers, choose the correct blocks of text, then run:\n"
            "  git add <each resolved file>\n"
            "  python scripts/generate_appinventor_project.py\n"
            "Once the helper succeeds you can commit and continue your merge or rebase."
        )


def ensure_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / ".nomedia").write_text("")


def ensure_project_properties() -> None:
    YOUNG_DIR.mkdir(parents=True, exist_ok=True)
    (YOUNG_DIR / "project.properties").write_text(PROJECT_PROPERTIES)


def write_aia() -> None:
    with zipfile.ZipFile(AIA_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PROJECT_DIR.rglob("*")):
            if path.is_file() and path != AIA_PATH:
                archive.write(path, path.relative_to(PROJECT_DIR))


def main() -> None:
    ensure_required_files()
    ensure_no_conflicts()
    ensure_assets()
    ensure_project_properties()
    write_aia()


if __name__ == "__main__":
    main()
