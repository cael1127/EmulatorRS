"""Export software framebuffer to ASCII or PPM (no third-party deps)."""

from __future__ import annotations


def index_to_rgb(index: int) -> tuple[int, int, int]:
    """Map 8-bit palette index to RGB for visualization."""
    i = index & 0xFF
    if i == 0:
        return (16, 16, 24)
    r = (i * 37 + 40) % 256
    g = (i * 17 + 80) % 256
    b = (i * 97 + 120) % 256
    return (r, g, b)


def framebuffer_to_ascii(
    framebuffer: list[list[int]],
    *,
    empty: str = ".",
    density: str = " .:-=+*#%@",
) -> str:
    """
    One character per pixel; darker indices use earlier chars in ``density``.
    """
    if not framebuffer:
        return ""
    lines: list[str] = []
    for row in framebuffer:
        chars: list[str] = []
        for idx in row:
            i = idx & 0xFF
            if i == 0:
                chars.append(empty)
            else:
                pos = min(len(density) - 1, max(1, i * len(density) // 256))
                chars.append(density[pos])
        lines.append("".join(chars))
    return "\n".join(lines) + "\n"


def framebuffer_to_ppm(framebuffer: list[list[int]]) -> bytes:
    """Binary P6 PPM (RGB 8-bit), viewable in many viewers and browsers."""
    if not framebuffer:
        return b"P6\n0 0\n255\n"
    height = len(framebuffer)
    width = len(framebuffer[0])
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    body = bytearray(width * height * 3)
    p = 0
    for row in framebuffer:
        if len(row) != width:
            raise ValueError("framebuffer rows must have uniform width")
        for idx in row:
            r, g, b = index_to_rgb(idx)
            body[p] = r
            body[p + 1] = g
            body[p + 2] = b
            p += 3
    return header + bytes(body)
