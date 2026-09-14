"""Trace the Frontline Systems logo PNG into clean two-colour SVG paths.

There is no potrace in this container, so: build float ink-coverage maps from the
source, supersample them, threshold, then walk the crack boundary between filled and
empty cells and simplify each loop with Ramer-Douglas-Peucker.

The supersample step is the point. The source mark is only ~420px wide, so tracing its
pixel grid directly gives visibly faceted diagonals. But the PNG is antialiased, and a
half-covered edge pixel carries half the ink - so coverage recovers sub-pixel edge
positions that the pixel grid alone throws away.
"""
import sys

import numpy as np
from PIL import Image

sys.setrecursionlimit(50000)

SRC = 'logo-orig.png'
NAVY, CHARCOAL = '#1F3470', '#2C2C2C'
SS = 6                     # supersample factor
EPS = 0.9                  # RDP tolerance, in source pixels

a = np.array(Image.open(SRC).convert('RGBA')).astype(float)
r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
alpha = al / 255.0

# The logo sits on opaque white in places and on transparency in others, so neither
# alpha nor darkness alone separates ink from background. Two independent measures do:
#
#   ink   - how far the pixel is from white, via its minimum channel. White gives 0,
#           charcoal and navy both give 1, and any blend lands proportionally between.
#   blue  - how much blue exceeds the red/green average. This is ~70 for navy and
#           exactly 0 for BOTH white and charcoal, so it reads navy's share cleanly
#           whether navy is blending into white at an outer edge or into charcoal at
#           the interior seam. That is what the earlier axis-projection got wrong:
#           charcoal blended toward white also drifts along the charcoal->navy axis.
ink = np.clip((255.0 - np.minimum(np.minimum(r, g), b)) / (255.0 - 44.0), 0, 1)
blue = np.clip((b - (r + g) / 2.0) / 70.5, 0, 1)

cov_navy = alpha * np.minimum(blue, ink)
cov_dark = alpha * np.clip(ink - blue, 0, 1)

ys, xs = np.where((cov_navy + cov_dark) > 0.5)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
cov_navy, cov_dark = cov_navy[y0:y1, x0:x1], cov_dark[y0:y1, x0:x1]
h0, w0 = cov_navy.shape


def upsample(c):
    im = Image.fromarray(c.astype(np.float32), mode='F')
    return np.array(im.resize((w0 * SS, h0 * SS), Image.BICUBIC)) > 0.5


is_navy, is_dark = upsample(cov_navy), upsample(cov_dark)
print(f'mark {w0}x{h0}  ->  traced at {w0*SS}x{h0*SS}   '
      f'navy {is_navy.sum()}  dark {is_dark.sum()}')


def loops(mask):
    """Chain the filled/empty boundary into closed rectilinear loops.

    Each filled cell contributes a directed unit edge for every side facing empty
    space, wound so the fill is always on the same hand. Outer contours come out
    clockwise and holes anticlockwise, which is what SVG's nonzero fill rule wants.
    """
    m = np.zeros((mask.shape[0] + 2, mask.shape[1] + 2), bool)
    m[1:-1, 1:-1] = mask
    edges = {}
    ys, xs = np.where(m)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if not m[y - 1, x]: edges.setdefault((x, y), []).append((x + 1, y))
        if not m[y, x + 1]: edges.setdefault((x + 1, y), []).append((x + 1, y + 1))
        if not m[y + 1, x]: edges.setdefault((x + 1, y + 1), []).append((x, y + 1))
        if not m[y, x - 1]: edges.setdefault((x, y + 1), []).append((x, y))
    out = []
    while edges:
        start = next(iter(edges))
        loop, p = [start], start
        while True:
            nxts = edges.get(p)
            if not nxts:
                break
            q = nxts.pop()
            if not nxts: del edges[p]
            if q == start:
                break
            loop.append(q); p = q
        if len(loop) > 4 * SS:          # drop specks left by thresholding
            out.append([(x - 1, y - 1) for x, y in loop])
    return out


def rdp(pts, eps):
    if len(pts) < 3: return pts
    p0, p1 = np.array(pts[0], float), np.array(pts[-1], float)
    seg = p1 - p0
    L = float(np.hypot(*seg))
    P = np.array(pts, float)
    V = P - p0
    d = np.hypot(*V.T) if L < 1e-9 else np.abs(seg[0] * V[:, 1] - seg[1] * V[:, 0]) / L
    i = int(d.argmax())
    if d[i] > eps:
        return rdp(pts[:i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


def to_path(mask):
    fmt = lambda v: f'{v / SS:.2f}'.rstrip('0').rstrip('.')
    segs, pts = [], []
    for lp in loops(mask):
        s = rdp(lp + [lp[0]], EPS * SS)
        if len(s) < 4: continue
        pts += s[:-1]
        segs.append(f'M{fmt(s[0][0])} {fmt(s[0][1])}'
                    + ''.join(f'L{fmt(x)} {fmt(y)}' for x, y in s[1:-1]) + 'Z')
    return ''.join(segs), pts


(d_dark, p_dark), (d_navy, p_navy) = to_path(is_dark), to_path(is_navy)
print(f'dark path {len(d_dark)} chars   navy path {len(d_navy)} chars')

# Derive the viewBox from the paths that actually got emitted, not from the coverage
# map: thresholding and simplification both move edges, and the source carries a soft
# drop shadow that survives into the coverage bounds. A loose viewBox would silently
# pad the logo with dead space wherever it is laid out.
P = np.array(p_dark + p_navy, float) / SS
vx, vy = P[:, 0].min(), P[:, 1].min()
vw, vh = P[:, 0].max() - vx, P[:, 1].max() - vy
VB = f'{vx:.2f} {vy:.2f} {vw:.2f} {vh:.2f}'
print(f'viewBox {VB}   (coverage bounds were {w0}x{h0})')


def svg(dark_fill, navy_fill):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w0} {h0}" '
            f'role="img" aria-label="Frontline Systems">'
            f'<path fill="{dark_fill}" d="{d_dark}"/>'
            f'<path fill="{navy_fill}" d="{d_navy}"/></svg>')


open('frontline-mark.svg', 'w').write(svg(CHARCOAL, NAVY))
open('frontline-mark-light.svg', 'w').write(svg('#FFFFFF', NAVY))

# The square lockup: white F/S and navy chevron inside a charcoal rounded square.
S = 512
sc = (S * 0.62) / vw
tx, ty = (S - vw * sc) / 2 - vx * sc, (S - vh * sc) / 2 - vy * sc
open('frontline-icon.svg', 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" role="img" '
    f'aria-label="Frontline Systems">'
    f'<rect width="{S}" height="{S}" rx="{round(S * 0.145)}" fill="{CHARCOAL}"/>'
    f'<g transform="translate({tx:.2f} {ty:.2f}) scale({sc:.5f})">'
    f'<path fill="#FFFFFF" d="{d_dark}"/><path fill="{NAVY}" d="{d_navy}"/></g></svg>')

for f in ('frontline-mark.svg', 'frontline-mark-light.svg', 'frontline-icon.svg'):
    print(f'{f:28} {len(open(f).read()) / 1024:.1f} KB')
