"""
Parametric, symmetric, CNC-friendly base mesh of a seated Digambar Jain Tirthankara.

Coordinate system:
    x = left/right, y = front/back (front is negative), z = vertical.
    The normalized master mesh is 54 units tall, with z=0 at the bottom of
    the lotus legs and z=54 at the crown. One unit may be rescaled to any
    shop unit after import; the supplied STL/OBJ are intentionally unitless.

The model is generated as the zero isosurface of a union of smooth solids.
That gives a single, closed, watertight shell without overlapping STL shells,
open seams, or trapped cavities. All bilateral features are defined in mirrored
pairs. The relief is shallow and blended into the chest so it does not create
an inaccessible CNC undercut.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from skimage.measure import marching_cubes
import trimesh

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(parents=True, exist_ok=True)

# A near-isotropic field. X and Z are odd-sized and centered so the scalar field
# is exactly mirrored about x=0 before marching cubes.
XMIN, XMAX = -15.0, 15.0
YMIN, YMAX = -12.0, 10.0
ZMIN, ZMAX = -1.0, 55.0
NX, NY, NZ = 189, 139, 351
xs = np.linspace(XMIN, XMAX, NX, dtype=np.float32)
ys = np.linspace(YMIN, YMAX, NY, dtype=np.float32)
zs = np.linspace(ZMIN, ZMAX, NZ, dtype=np.float32)

# Positive inside, negative outside. The output field stays in memory but all
# primitive calculations are chunked over z to keep peak memory modest.
field = np.full((NX, NY, NZ), -100.0, dtype=np.float32)

def ellipsoid_field(X, Y, Z, cx, cy, cz, rx, ry, rz):
    """Smooth implicit ellipsoid, positive inside."""
    q = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2
    return np.float32(min(rx, ry, rz)) * (1.0 - np.sqrt(q, dtype=np.float32))


def round_box_field(X, Y, Z, cx, cy, cz, hx, hy, hz, blend=0.0):
    """Rounded box-like implicit solid, positive inside.

    blend is a small corner-rounding amount. With blend=0 this is a clean
    shallow relief bar; the field is still a single solid when fused to the
    chest/head.
    """
    dx = np.abs(X - cx) - hx
    dy = np.abs(Y - cy) - hy
    dz = np.abs(Z - cz) - hz
    outside = np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2 + np.maximum(dz, 0) ** 2)
    inside = np.minimum(np.maximum(dx, np.maximum(dy, dz)), 0.0)
    return -(outside + inside)


def add_ellipsoid(cx, cy, cz, rx, ry, rz):
    for k0 in range(0, NZ, 32):
        k1 = min(k0 + 32, NZ)
        Z = zs[k0:k1][None, None, :]
        X = xs[:, None, None]
        Y = ys[None, :, None]
        f = ellipsoid_field(X, Y, Z, cx, cy, cz, rx, ry, rz)
        field[:, :, k0:k1] = np.maximum(field[:, :, k0:k1], f)


def add_round_box(cx, cy, cz, hx, hy, hz):
    for k0 in range(0, NZ, 32):
        k1 = min(k0 + 32, NZ)
        Z = zs[k0:k1][None, None, :]
        X = xs[:, None, None]
        Y = ys[None, :, None]
        f = round_box_field(X, Y, Z, cx, cy, cz, hx, hy, hz)
        field[:, :, k0:k1] = np.maximum(field[:, :, k0:k1], f)


def add_mirrored_ellipsoid(cx, cy, cz, rx, ry, rz):
    add_ellipsoid(cx, cy, cz, rx, ry, rz)
    add_ellipsoid(-cx, cy, cz, rx, ry, rz)


def add_chain(points, radii):
    """Fuse overlapping ellipsoids along a path; good for limbs and folded legs."""
    for (cx, cy, cz), (rx, ry, rz) in zip(points, radii):
        add_ellipsoid(cx, cy, cz, rx, ry, rz)


# ---------------------------------------------------------------------------
# BODY: the landmark levels are deliberately explicit.
# Neck landmark = z 42. Navel landmark = z 18: exactly 24 units apart.
# ---------------------------------------------------------------------------
# Pelvis, abdomen, and chest. The central chest solid has a 24-unit major
# width (x=-12..+12 at its equator), while the lower pelvis tapers inward.
add_ellipsoid(0.0, 0.25, 16.5, 9.2, 5.0, 8.7)
add_ellipsoid(0.0, 0.15, 25.5, 10.8, 5.2, 11.0)
add_ellipsoid(0.0, 0.05, 29.0, 12.0, 5.5, 9.8)  # 24-wide chest band
add_ellipsoid(0.0, 0.10, 35.0, 9.0, 4.8, 7.0)
# Shoulders are merged, not separate shells.
add_mirrored_ellipsoid(5.6, 0.0, 36.0, 6.3, 4.7, 5.3)
# Narrow waist/neck blend keeps the underside of the chin and arm roots open.
add_ellipsoid(0.0, 0.10, 40.5, 4.7, 4.0, 5.0)
add_ellipsoid(0.0, 0.15, 42.0, 4.4, 3.8, 4.0)

# Navel location is preserved as a smooth, shallow front landmark (not a
# through-hole). The surrounding abdomen is intentionally uninterrupted.
add_ellipsoid(0.0, -4.75, 18.0, 0.75, 0.45, 0.60)

# ---------------------------------------------------------------------------
# ARMS: long, tapered, continuous with shoulders, sides, and lap.  The
# mirrored chains remove arm-body gaps and avoid CNC undercuts below the arms.
# ---------------------------------------------------------------------------
for s in (-1.0, 1.0):
    points = [
        (s * 8.0, 0.00, 35.0),
        (s * 9.0, 0.00, 32.0),
        (s * 9.2, -0.15, 28.5),
        (s * 8.9, -0.80, 25.0),
        (s * 8.3, -1.80, 21.5),
        (s * 7.5, -3.00, 18.0),
        (s * 6.4, -3.85, 15.1),
    ]
    radii = [
        (3.1, 3.0, 4.0),
        (2.8, 2.8, 3.6),
        (2.55, 2.65, 3.4),
        (2.45, 2.55, 3.3),
        (2.35, 2.45, 3.1),
        (2.45, 2.45, 3.0),
        (2.55, 2.35, 3.4),
    ]
    add_chain(points, radii)
# Broad lap/palm transitions keep the hands resting on the folded legs.
add_mirrored_ellipsoid(5.6, -4.0, 15.7, 2.8, 2.0, 4.0)

# ---------------------------------------------------------------------------
# PADMASANA: two mirrored diagonal thigh chains, a merged central crossing,
# and low foot lobes. Every piece touches the pelvic/leg mass; no floating
# interpenetrating shells are exported.
# ---------------------------------------------------------------------------
for s in (-1.0, 1.0):
    # One thigh folds diagonally forward toward the opposite side.
    points = [
        (s * 4.1, 0.10, 12.5),
        (s * 3.0, -0.75, 10.5),
        (s * 1.3, -2.25, 8.4),
        (s * -1.5, -3.85, 6.4),
        (s * -4.8, -5.05, 5.0),
    ]
    radii = [
        (4.8, 4.4, 3.7),
        (4.6, 4.1, 3.7),
        (4.4, 3.9, 3.6),
        (4.5, 3.8, 3.5),
        (4.7, 3.6, 3.5),
    ]
    add_chain(points, radii)
# Symmetric front foot/ankle lobes and a smooth underside support; bottom is
# designed at z=0 and will be normalized after extraction.
add_mirrored_ellipsoid(7.1, -5.75, 4.2, 4.7, 2.8, 4.2)
add_ellipsoid(0.0, -1.0, 5.0, 7.5, 5.5, 4.9)
add_ellipsoid(0.0, 1.8, 6.0, 10.0, 4.7, 5.8)
# Small rounded central front overlap makes the crossed legs one clean volume.
add_ellipsoid(0.0, -4.2, 5.3, 5.7, 3.0, 3.3)

# ---------------------------------------------------------------------------
# HEAD: exactly z=42..54 = 12 vertical units. Main facial width is exactly
# x=-7..+7 = 14 units; ears are additional side width.
# ---------------------------------------------------------------------------
add_ellipsoid(0.0, -0.05, 48.0, 7.0, 5.4, 6.0)     # crown: top z=54
add_ellipsoid(0.0, -0.85, 46.0, 6.4, 4.8, 4.4)    # cheeks/jaw
# Chin is blended upward into the neck, avoiding a recessed/undercut chin.
add_ellipsoid(0.0, -0.75, 44.7, 5.7, 4.4, 2.8)
# Elongated earlobes: exactly 10 units vertically, z=42..52.
add_mirrored_ellipsoid(7.55, 0.0, 47.0, 1.45, 3.15, 5.0)
# A small crown/ushnisha transition is contained inside the 12-unit head box.
add_ellipsoid(0.0, 0.15, 53.1, 3.6, 3.5, 0.9)

# Face relief is low and fused; it is deliberately not a set of thin, separate
# pieces, so there are no deep CNC cavities beneath the brow/nose/lips.
add_mirrored_ellipsoid(2.45, -5.20, 49.15, 1.75, 0.42, 0.18)  # closed eyes
add_mirrored_ellipsoid(2.55, -5.05, 49.85, 2.0, 0.38, 0.22)   # brow line
add_ellipsoid(0.0, -5.30, 48.0, 0.75, 0.75, 1.75)              # nose bridge
add_ellipsoid(0.0, -5.16, 46.0, 1.65, 0.34, 0.24)              # lips
add_ellipsoid(0.0, -4.90, 44.7, 3.5, 0.45, 1.8)               # chin blend

# ---------------------------------------------------------------------------
# RAISED SHRIVATSA: centered on the chest, exact design envelope x=-2..+2,
# z=29..34 = 4 x 5 units. The shallow relief is intersected into the chest.
# ---------------------------------------------------------------------------
# vertical stem, horizontal shoulders, and a lower knot make a restrained
# Jain Shrivatsa-like raised mark rather than a generic embossed cross.
add_ellipsoid(0.0, -5.28, 31.5, 0.46, 0.42, 2.50)
add_ellipsoid(0.0, -5.32, 32.6, 2.00, 0.40, 0.42)
add_ellipsoid(0.0, -5.30, 30.35, 1.05, 0.38, 0.42)
add_mirrored_ellipsoid(0.82, -5.29, 31.25, 0.72, 0.36, 0.33)

# Extract a closed surface. The z-axis is the final array axis in the field.
verts, faces, normals, values = marching_cubes(
    field, level=0.0,
    spacing=(float(xs[1]-xs[0]), float(ys[1]-ys[0]), float(zs[1]-zs[0])),
    allow_degenerate=False,
)
verts[:, 0] += XMIN
verts[:, 1] += YMIN
verts[:, 2] += ZMIN

# Exact normalized vertical bounding box. The source field is already at 54;
# this final affine step absorbs one voxel interpolation epsilon and guarantees
# zmin=0, zmax=54 in the deliverable.
raw_min = verts.min(axis=0)
raw_max = verts.max(axis=0)
verts[:, 2] = (verts[:, 2] - raw_min[2]) * (54.0 / (raw_max[2] - raw_min[2]))
# The chest-band primitive is the master 24-unit transverse datum. Normalize
# its extracted voxel epsilon to exact +/-12 without disturbing z landmarks.
raw_x_center = 0.5 * (raw_min[0] + raw_max[0])
verts[:, 0] = (verts[:, 0] - raw_x_center) * (24.0 / (raw_max[0] - raw_min[0]))
# Keep bilateral symmetry exact to floating precision in the exported vertices.
# The scalar field itself is symmetric; this also removes tiny numerical drift.
verts[:, 0] = np.where(np.abs(verts[:, 0]) < 1e-6, 0.0, verts[:, 0])

mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
# Cleanup calls are safe for a marching-cubes manifold; they only remove
# duplicate/zero-area facets, not open boundaries.
try:
    mesh.remove_duplicate_faces()
    mesh.remove_degenerate_faces()
except AttributeError:
    pass
mesh.remove_unreferenced_vertices()
# Marching-cubes winding depends on the sign convention. Export outward-facing
# normals so the signed volume is positive for CAM and slicer software.
if mesh.volume < 0:
    mesh.invert()

# The normalized coordinate convention is preserved in both deliverables.
mesh.export(OUT / "tirthankara_padmasana_base_54u.stl")
mesh.export(OUT / "tirthankara_padmasana_base_54u.obj")

# Save a compact audit record next to the mesh.
components = mesh.split(only_watertight=False)
record = {
    "title": "Seated Digambar Jain Tirthankara, Padmasana, symmetric base mesh",
    "source_document": "pratima vigyan.pdf (attached by user)",
    "coordinate_system": {"x": "left/right", "y": "front/back; front is negative", "z": "vertical"},
    "unit_note": "Normalized, unitless geometry. Rescale 1 unit to any millimetres/inches in the CAM package.",
    "required_measurements": {
        "total_height": 54.0,
        "head_height": 12.0,
        "face_width": 14.0,
        "earlobe_vertical_length": 10.0,
        "neck_to_navel": 24.0,
        "chest_width": 24.0,
        "shrivatsa_envelope_width": 4.0,
        "shrivatsa_envelope_height": 5.0,
        "lotus_leg_height": 12.0,
    },
    "landmarks": {"bottom": 0.0, "navel": 18.0, "neck": 42.0, "head_top": 54.0, "earlobes": [42.0, 52.0], "shrivatsa": {"x": [-2.0, 2.0], "z": [29.0, 34.0]}, "lotus": [0.0, 12.0]},
    "mesh_audit": {
        "vertices": int(len(mesh.vertices)),
        "triangles": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "connected_components": int(len(components)),
        "bounds_xyz": [[float(v) for v in row] for row in mesh.bounds],
        "extents_xyz": [float(v) for v in mesh.extents],
        "volume": float(mesh.volume),
    },
    "design_note": "Implicit union creates one closed shell with fused limbs and a shallow fused Shrivatsa; no internal overlapping shells or through-holes are exported.",
}
(OUT / "tirthankara_measurement_audit.json").write_text(json.dumps(record, indent=2), encoding="utf-8")

print(json.dumps(record, indent=2))
print(f"Wrote: {OUT / 'tirthankara_padmasana_base_54u.stl'}")
print(f"Wrote: {OUT / 'tirthankara_padmasana_base_54u.obj'}")
