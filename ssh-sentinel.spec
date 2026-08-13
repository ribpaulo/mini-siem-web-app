"""PyInstaller-Konfiguration für Linux und Windows."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH)

# Templates, CSS und JavaScript werden neben den Python-Modulen in das interne
# Bundle aufgenommen. PyInstaller stellt sie bei --onefile zur Laufzeit bereit.
data_files = [
    (str(project_root / "templates"), "templates"),
    (str(project_root / "static"), "static"),
]

# Uvicorn lädt Protokoll- und Loop-Implementierungen über Import-Strings. Die
# Submodule müssen PyInstaller deshalb ausdrücklich bekannt gemacht werden.
hidden_imports = collect_submodules("uvicorn")

analysis = Analysis(
    [str(project_root / "launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="ssh-sentinel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
