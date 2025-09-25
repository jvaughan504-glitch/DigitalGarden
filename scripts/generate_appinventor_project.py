#!/usr/bin/env python3
"""Package the MIT App Inventor project into an AIA archive.

This helper rewrites the small bits of metadata that are deterministic and then
zips the checked-in source tree under ``app_inventor/DigitalGardenController``.
The generated ``DigitalGardenController.aia`` can be imported directly into MIT
App Inventor.  Running the script repeatedly is safe.
"""

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


def ensure_required_files() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        missing_text = "\n".join(f"  - {item}" for item in missing)
        raise FileNotFoundError(
            "The MIT App Inventor sources are incomplete. Make sure the following files exist:\n"
            f"{missing_text}\n"
            "If they were deleted, restore them with `git checkout -- app_inventor`."
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
    ensure_assets()
    ensure_project_properties()
    write_aia()


if __name__ == "__main__":
    main()
