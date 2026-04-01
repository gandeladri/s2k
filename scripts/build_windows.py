import shutil
import subprocess
import sys
from pathlib import Path


APP_SCRIPT = "run_windows.py"
ICON_FILE = Path("assets/icons/s2k.ico")
EXE_NAME = "s2k"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        print(f"Removed folder: {path.relative_to(project_root())}")
        return

    if path.exists():
        path.unlink()
        print(f"Removed file: {path.relative_to(project_root())}")


def build_windows() -> int:
    root = project_root()

    build_dir = root / "build"
    dist_dir = root / "dist"
    spec_file = root / f"{EXE_NAME}.spec"
    app_file = root / APP_SCRIPT
    icon_file = root / ICON_FILE

    if not app_file.exists():
        print(f"ERROR: Could not find {APP_SCRIPT} in:\n{root}")
        return 1

    if not icon_file.exists():
        print(f"ERROR: Could not find {ICON_FILE.as_posix()} in:\n{root}")
        return 1

    print("Cleaning previous windows build artifacts...")
    remove_path(build_dir)
    remove_path(dist_dir)
    remove_path(spec_file)

    cmd = [
        "pyinstaller",
        "--paths",
        ".",
        "--clean",
        "--onefile",
        "--noconsole",
        "--name",
        EXE_NAME,
        "--icon",
        ICON_FILE.as_posix(),
        "--hidden-import",
        "frontend",
        "--hidden-import",
        "frontend.windows",
        "--hidden-import",
        "frontend.windows.app",
        "--hidden-import",
        "frontend.windows.bootstrap",
        "--hidden-import",
        "frontend.windows.settings_manager",
        "--hidden-import",
        "frontend.windows.tts_utils",
        "--hidden-import",
        "core",
        "--hidden-import",
        "core.constants",
        "--hidden-import",
        "core.converter",
        "--hidden-import",
        "core.katakana_client",
        "--hidden-import",
        "core.phonetics",
        "--hidden-import",
        "winrt.windows.foundation",
        "--hidden-import",
        "winrt.windows.foundation.collections",
        "--hidden-import",
        "winrt.windows.media.core",
        "--hidden-import",
        "winrt.windows.media.playback",
        "--hidden-import",
        "winrt.windows.media.speechsynthesis",
        "--hidden-import",
        "winrt.windows.storage.streams",
        "--add-data",
        f"{ICON_FILE.as_posix()};assets/icons",
        APP_SCRIPT,
    ]

    print("\nRunning windows build:")
    print(" ".join(cmd))
    print()

    try:
        subprocess.run(cmd, check=True, cwd=root)
    except FileNotFoundError:
        print("ERROR: pyinstaller is not installed or is not in PATH.")
        print("Install it with: pip install pyinstaller")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: Windows build failed with exit code {exc.returncode}.")
        return exc.returncode

    exe_path = dist_dir / f"{EXE_NAME}.exe"
    print()
    if exe_path.exists():
        print(f"Windows build completed successfully: {exe_path}")
        return 0

    print("Windows build finished, but the exe was not found in dist.")
    return 1


if __name__ == "__main__":
    sys.exit(build_windows())
