#!/usr/bin/env python3
"""Generate the full Rustogram icon set from rustogram.svg.

Produces:
- icons/art/                  — 15 PNG files for Telegram/Resources/art/
- icons/art/icon256.ico       — Windows multi-resolution .ico
- icons/AppIcon.appiconset/   — 10 PNG files for macOS bundle icon
- icons/Icon.iconset/         — 10 PNG files (alt naming for iconutil)

Master sources (in repo root):
- rustogram.svg                       — vector, no text  (used for app icon)
- main_logo_1024_transparent.png      — raster, with text (splash; copied as-is)

Requires: inkscape (system), Pillow (pip).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
SVG = ROOT / 'rustogram.svg'
OUT = ROOT / 'icons'

# Render the SVG once at every unique size we need, cache the result.
UNIQUE_SIZES = [16, 32, 48, 64, 96, 128, 256, 512, 1024]

# Group 1: Telegram/Resources/art/  (PNG variants)
ART = {
    'icon16.png':       16,  'icon16@2x.png':   32,
    'icon32.png':       32,  'icon32@2x.png':   64,
    'icon48.png':       48,  'icon48@2x.png':   96,
    'icon64.png':       64,  'icon64@2x.png':  128,
    'icon128.png':     128,  'icon128@2x.png': 256,
    'icon256.png':     256,  'icon256@2x.png': 512,
    'icon512.png':     512,  'icon512@2x.png': 1024,
}

# Group 3: macOS AppIcon.appiconset/
APPICON = {
    'icon16.png':   16,  'icon16@2x.png':   32,
    'icon32.png':   32,  'icon32@2x.png':   64,
    'icon128.png': 128,  'icon128@2x.png': 256,
    'icon256.png': 256,  'icon256@2x.png': 512,
    'icon512.png': 512,  'icon512@2x.png': 1024,
}

# Group 4: macOS Icon.iconset/
ICONSET = {
    'icon_16x16.png':    16,  'icon_16x16@2x.png':   32,
    'icon_32x32.png':    32,  'icon_32x32@2x.png':   64,
    'icon_128x128.png': 128,  'icon_128x128@2x.png': 256,
    'icon_256x256.png': 256,  'icon_256x256@2x.png': 512,
    'icon_512x512.png': 512,  'icon_512x512@2x.png': 1024,
}

# Sizes packed into Windows multi-resolution .ico
ICO_SIZES = [16, 32, 48, 64, 128, 256]


def render_svg(size: int, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'inkscape', str(SVG),
        '--export-type=png',
        f'--export-filename={out_path}',
        f'--export-width={size}',
        f'--export-height={size}',
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    if not SVG.exists():
        print(f'ERROR: master not found: {SVG}', file=sys.stderr)
        return 1

    if OUT.exists():
        shutil.rmtree(OUT)

    cache_dir = OUT / '.cache'
    cache_dir.mkdir(parents=True)

    print(f'Rendering {len(UNIQUE_SIZES)} unique sizes from {SVG.name}...')
    cache: dict[int, Path] = {}
    for size in UNIQUE_SIZES:
        out = cache_dir / f'{size}.png'
        render_svg(size, out)
        cache[size] = out
        print(f'  {size}x{size} -> cached')

    def materialize(group: dict[str, int], target: Path, label: str) -> None:
        target.mkdir(parents=True, exist_ok=True)
        for name, size in group.items():
            shutil.copy2(cache[size], target / name)
        print(f'  {label}: {len(group)} files -> {target.relative_to(ROOT)}')

    print('Materializing PNG groups...')
    materialize(ART,     OUT / 'art',                'art/')
    materialize(APPICON, OUT / 'AppIcon.appiconset', 'AppIcon.appiconset/')
    materialize(ICONSET, OUT / 'Icon.iconset',       'Icon.iconset/')

    print('Building Windows multi-resolution .ico...')
    base = Image.open(cache[256])
    ico_path = OUT / 'art' / 'icon256.ico'
    base.save(ico_path, sizes=[(s, s) for s in ICO_SIZES])
    print(f'  {ico_path.relative_to(ROOT)} ({", ".join(f"{s}x{s}" for s in ICO_SIZES)})')

    shutil.rmtree(cache_dir)

    total = len(ART) + len(APPICON) + len(ICONSET) + 1
    print(f'\nDone. {total} files generated in {OUT.relative_to(ROOT)}/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
