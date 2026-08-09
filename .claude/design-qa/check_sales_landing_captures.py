"""Fail closed when a sales-landing evidence capture contains no page content."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent

GROUPS = {
    "mobile": [
        "sales-landing-problem-first-mobile.png",
        "sales-landing-mechanism-first-mobile.png",
        "sales-landing-adoption-first-mobile.png",
    ],
    "desktop": [
        "sales-landing-problem-first-desktop.png",
        "sales-landing-mechanism-first-desktop.png",
        "sales-landing-adoption-first-desktop.png",
    ],
    "comparison": ["sales-landing-mobile-comparison.png"],
}

MINIMUMS = {
    "mobile": (350, 700),
    "desktop": (1100, 600),
    "comparison": (1400, 700),
}


def inspect_capture(group: str, name: str) -> tuple[str, str]:
    path = ROOT / name
    if not path.is_file():
        raise AssertionError(f"missing capture: {name}")

    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest().upper()
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        min_width, min_height = MINIMUMS[group]
        assert width >= min_width and height >= min_height, (
            f"{name}: {width}x{height} is below {min_width}x{min_height}"
        )

        gray = rgb.convert("L")
        histogram = gray.histogram()
        pixel_count = width * height
        dark_ratio = sum(histogram[:120]) / pixel_count
        entropy = rgb.entropy()
        colors = rgb.getcolors(maxcolors=pixel_count)
        color_count = len(colors) if colors is not None else pixel_count

        assert dark_ratio >= 0.01, (
            f"{name}: dark-pixel ratio {dark_ratio:.5f} shows no readable ink"
        )
        assert entropy >= 4.0, (
            f"{name}: entropy {entropy:.3f} is consistent with a blank canvas"
        )
        assert color_count >= 1000, (
            f"{name}: only {color_count} colors, consistent with a blank canvas"
        )

    summary = (
        f"{name}: {width}x{height} entropy={entropy:.3f} "
        f"dark={dark_ratio:.5f} colors={color_count} sha256={digest}"
    )
    return digest, summary


def main() -> None:
    for group, names in GROUPS.items():
        digests: set[str] = set()
        for name in names:
            digest, summary = inspect_capture(group, name)
            assert digest not in digests, f"{group}: duplicate capture {name}"
            digests.add(digest)
            print(summary)
    print("sales-landing capture content checks: PASS")


if __name__ == "__main__":
    main()
