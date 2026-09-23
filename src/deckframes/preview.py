"""Render a .pptx to per-slide PNGs + one contact-sheet grid for visual QA.

Backends, first available wins:
  1. Microsoft PowerPoint via COM (Windows)          — exact fonts/rendering
  2. LibreOffice (soffice) → PDF → PyMuPDF / pdftoppm — Windows, macOS, Linux
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

SOFFICE_CANDIDATES = [
    "soffice", "libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def find_soffice() -> str | None:
    for c in SOFFICE_CANDIDATES:
        p = shutil.which(c) or (c if Path(c).exists() else None)
        if p:
            return p
    return None


def has_powerpoint() -> bool:
    if sys.platform != "win32":
        return False
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "[bool](Get-ItemProperty 'Registry::HKEY_CLASSES_ROOT\\PowerPoint.Application' -ErrorAction SilentlyContinue)"],
                       capture_output=True, text=True)
    return r.stdout.strip().lower() == "true"


def via_powerpoint(pptx: Path, out: Path) -> bool:
    if sys.platform != "win32":
        return False
    ps = ("$pp = New-Object -ComObject PowerPoint.Application; "
          f"$p = $pp.Presentations.Open('{pptx}', $true, $false, $false); "
          f"$p.SaveAs('{out}', 18); $p.Close(); $pp.Quit()")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    pngs = [f for f in out.iterdir() if f.suffix.lower() == ".png"]  # PowerPoint names them per UI language
    for i, f in enumerate(sorted(pngs, key=lambda f: int(re.findall(r"(\d+)", f.stem)[-1])), 1):
        f.rename(out / f"slide-{i:03d}.png")
    return r.returncode == 0 and bool(pngs)


def via_libreoffice(pptx: Path, out: Path) -> bool:
    soffice = find_soffice()
    if not soffice:
        return False
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(pptx)],
                   capture_output=True, timeout=300)
    pdf = out / (pptx.stem + ".pdf")
    if not pdf.exists():
        return False
    try:
        try:
            import pymupdf
        except ImportError:
            import fitz as pymupdf
        for n, page in enumerate(pymupdf.open(pdf), 1):
            page.get_pixmap(dpi=110).save(out / f"slide-{n:03d}.png")
        return True
    except ImportError:
        if shutil.which("pdftoppm"):
            subprocess.run(["pdftoppm", "-png", "-r", "110", str(pdf), str(out / "slide")], capture_output=True)
            for f in out.glob("slide-*.png"):
                n = int(re.findall(r"(\d+)", f.stem)[-1])
                f.rename(out / f"slide-{n:03d}.png")
            return True
    return False


def render(pptx: Path, out: Path | None = None, cols: int = 4, backend: str = "auto") -> dict:
    pptx = pptx.resolve()
    out = (out or pptx.parent / f"{pptx.stem}_preview").resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    order = {"auto": (via_powerpoint, via_libreoffice), "powerpoint": (via_powerpoint,),
             "libreoffice": (via_libreoffice,)}[backend]
    used = next((fn.__name__[4:] for fn in order if fn(pptx, out)), None)
    if not used:
        raise SystemExit("no renderer available: install LibreOffice (+ `pip install pymupdf`) or use PowerPoint on Windows")
    files = sorted(out.glob("slide-*.png"))
    w, h, gap = 480, 270, 10
    rows = -(-len(files) // cols)
    grid = Image.new("RGB", (cols * (w + gap) + gap, rows * (h + gap) + gap), "#888888")
    for k, f in enumerate(files):
        with Image.open(f) as im:
            grid.paste(im.convert("RGB").resize((w, h)),
                       (gap + (k % cols) * (w + gap), gap + (k // cols) * (h + gap)))
    grid_path = out / "grid.png"
    grid.save(grid_path)
    return {"backend": used, "slides": [str(f) for f in files], "grid": str(grid_path), "dir": str(out)}
