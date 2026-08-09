"""Bind sales-landing evidence to the exact captures inspected in review."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image


DEFAULT_ROOT = Path(__file__).resolve().parent

CAPTURES = {
    "mobile": [
        (
            "sales-landing-problem-first-mobile.png",
            (375, 812),
            "F095F6BB204268926F60C66169E0A2B4D874EF23FED0853AFCFA074C2A8FAF6A",
        ),
        (
            "sales-landing-mechanism-first-mobile.png",
            (375, 812),
            "5BB153DF1697824D619077EB4A98519CDF8F450A0E20056DEAAC1D0A63D18D5F",
        ),
        (
            "sales-landing-adoption-first-mobile.png",
            (375, 812),
            "9298A22BB2CA8B7299D18285CA8BBF13E2C499162C62FEB269771C65DF15FD80",
        ),
    ],
    "desktop": [
        (
            "sales-landing-problem-first-desktop.png",
            (1265, 712),
            "D12280FE83A0A906B93C7522586D8BF7FB93903EB49602E813A7998E78EFC386",
        ),
        (
            "sales-landing-mechanism-first-desktop.png",
            (1265, 712),
            "3BCA5B5CA5C0BFF17B6B1EE6B22D00DF0C94A118513ABBC62D0E38F03744DD4C",
        ),
        (
            "sales-landing-adoption-first-desktop.png",
            (1265, 712),
            "04697CC1CBB9FD9610BBAEAB2660F3AC279788844B2D971EA7D540BAE4EDE236",
        ),
    ],
    "comparison": [
        (
            "sales-landing-mobile-comparison.png",
            (1585, 854),
            "53916E14E50303B2E322CCDC7175503AA514ADED7CEC51A458A38045FBDBFB6C",
        )
    ],
}


def inspect_capture(
    root: Path, group: str, name: str, expected_size: tuple[int, int], expected_sha: str
) -> tuple[str, str]:
    path = root / name
    if not path.is_file():
        raise AssertionError(f"missing capture: {name}")

    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest().upper()
    assert digest == expected_sha, (
        f"{name}: SHA-256 mismatch; expected exact independently inspected "
        f"capture {expected_sha}, got {digest}"
    )

    with Image.open(path) as image:
        assert image.format == "PNG", f"{name}: expected PNG, got {image.format}"
        rgb = image.convert("RGB")
        assert rgb.size == expected_size, (
            f"{name}: expected {expected_size[0]}x{expected_size[1]}, "
            f"got {rgb.size[0]}x{rgb.size[1]}"
        )

        width, height = rgb.size
        gray = rgb.convert("L")
        histogram = gray.histogram()
        pixel_count = width * height
        dark_ratio = sum(histogram[:120]) / pixel_count
        entropy = rgb.entropy()
        colors = rgb.getcolors(maxcolors=pixel_count)
        color_count = len(colors) if colors is not None else pixel_count

    summary = (
        f"{name}: {width}x{height} entropy={entropy:.3f} "
        f"dark={dark_ratio:.5f} colors={color_count} sha256={digest}"
    )
    return digest, summary


def verify_all(root: Path = DEFAULT_ROOT) -> None:
    for group, specifications in CAPTURES.items():
        digests: set[str] = set()
        for name, expected_size, expected_sha in specifications:
            digest, summary = inspect_capture(
                root, group, name, expected_size, expected_sha
            )
            assert digest not in digests, f"{group}: duplicate capture {name}"
            digests.add(digest)
            print(summary)
    print("sales-landing capture provenance checks: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Directory containing the declared capture filenames.",
    )
    args = parser.parse_args()
    verify_all(args.root.resolve())


if __name__ == "__main__":
    main()
