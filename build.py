import shutil
import subprocess
import sys
from pathlib import Path


APP_SCRIPT = "s2k.py"
ICON_FILE = "s2k.ico"
EXE_NAME = "s2k"


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        print(f"Removed folder: {path.name}")
        return

    if path.exists():
        path.unlink()
        print(f"Removed file: {path.name}")


def main() -> int:
    root = Path(__file__).resolve().parent

    build_dir = root / "build"
    dist_dir = root / "dist"
    spec_file = root / f"{EXE_NAME}.spec"
    app_file = root / APP_SCRIPT
    icon_file = root / ICON_FILE

    if not app_file.exists():
        print(f"ERROR: Could not find {APP_SCRIPT} in:")
        print(root)
        return 1

    if not icon_file.exists():
        print(f"ERROR: Could not find {ICON_FILE} in:")
        print(root)
        return 1

    print("Cleaning previous build artifacts...")
    remove_path(build_dir)
    remove_path(dist_dir)
    remove_path(spec_file)

    cmd = [
        "pyinstaller",
        "--clean",
        "--onefile",
        "--noconsole",
        "--name",
        EXE_NAME,
        "--icon",
        ICON_FILE,
        "--add-data",
        f"{ICON_FILE};.",
        APP_SCRIPT,
    ]

    print("\nRunning:")
    print(" ".join(cmd))
    print()

    try:
        subprocess.run(cmd, check=True, cwd=root)
    except FileNotFoundError:
        print("ERROR: pyinstaller is not installed or is not in PATH.")
        print("Install it with: pip install pyinstaller")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: Build failed with exit code {exc.returncode}.")
        return exc.returncode

    exe_path = dist_dir / f"{EXE_NAME}.exe"

    print()
    if exe_path.exists():
        print(f"Build completed successfully: {exe_path}")
        return 0

    print("Build finished, but the exe was not found in dist.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
