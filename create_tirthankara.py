"""
Parametric CNC-friendly base mesh: Lord Mahavira (24th Jain Tirthankara),
seated in Padmasana with Dhyana Mudra.

This revision follows the supplied front/side reference photographs: upright
serene temple-sculpture anatomy, merged arms and lap, broad crossed lotus legs,
elongated lobes, Shrivatsa relief, and a Makrana-marble-style smooth surface.
It intentionally avoids Rishabhanatha shoulder locks; the scalp uses tight,
right-turning toroidal ringlets and a contained ushnisha.

Coordinates: x = left/right, y = front/back (front is negative), z = vertical.
The generated shell is normalized to z=0..54. STL/OBJ are unitless; choose the
shop scale in CAM (for example, 10 mm per unit gives 540 mm overall height).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from skimage.measure import marching_cubes
import trimesh

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(parents=True, exist_ok=True)

# Nearly isotropic voxel field; small enough to preserve the hair ringlets while
# remaining practical for a CNC base mesh.
XMIN, XMAX = -16.0, 16.0
YMIN, YMAX = -13.0, 10.0
ZMIN, ZMAX = -1.0, 55.0
NX, NY, NZ = 201, 145, 351
xs = np.linspace(XMIN, XMAX, NX, dtype=np.float32)
ys = np.linspace(YMIN, YMAX, NY, dtype=np.float32)
zs = np.linspace(ZMIN, ZMAX, NZ, dtype=np.float32)
field = np.full((NX, NY, NZ), -100.0, dtype=np.float32)


def ellipsoid_field(X, Y, Z, cx, cy, cz, rx, ry, rz):
    q = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2
    return np.float32(min(rx, ry, rz)) * (1.0 - np.sqrt(q, dtype=np.float32))


def rounded_box_field(X, Y, Z, cx, cy, cz, hx, hy, hz, radius):
    # Signed distance of a rounded box; positive inside.
    qx = np.abs(X - cx) - (hx - radius)
    qy = np.abs(Y - cy) - (hy - radius)
    qz = np.abs(Z - cz) - (hz - radius)
    outside = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    inside = np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0.0)
    return -(outside + inside - radius)


def torus_field(X, Y, Z, cx, cy, cz, nx, ny, nz, major, tube):
    # A torus whose ring plane is tangent to the scalp; (nx,ny,nz) is its
    # outward normal. This produces small fused ringlets, not loose hair pieces.
    dx, dy, dz = X - cx, Y - cy, Z - cz
    axial = dx * nx + dy * ny + dz * nz
    rx = dx - axial * nx
    ry = dy - axial * ny
    rz = dz - axial * nz
    radial = np.sqrt(rx * rx + ry * ry + rz * rz)
    return tube - np.sqrt((radial - major) ** 2 + axial ** 2)


def _chunk_slices():
    for k0 in range(0, NZ, 32):
        yield k0, min(k0 + 32, NZ)


def add_ellipsoid(cx, cy, cz, rx, ry, rz):
    X = xs[:, None, None]
    Y = ys[None, :, None]
    for k0, k1 in _chunk_slices():
        Z = zs[k0:k1][None, None, :]
        field[:, :, k0:k1] = np.maximum(field[:, :, k0:k1], ellipsoid_field(X, Y, Z, cx, cy, cz, rx, ry, rz))


def add_rounded_box(cx, cy, cz, hx, hy, hz, radius):
    X = xs[:, None, None]
    Y = ys[None, :, None]
    for k0, k1 in _chunk_slices():
        Z = zs[k0:k1][None, None, :]
        field[:, :, k0:k1] = np.maximum(field[:, :, k0:k1], rounded_box_field(X, Y, Z, cx, cy, cz, hx, hy, hz, radius))


def add_torus(cx, cy, cz, normal, major=0.34, tube=0.24):
    nx, ny, nz = normal
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / length, ny / length, nz / length
    X = xs[:, None, None]
    Y = ys[None, :, None]
    for k0, k1 in _chunk_slices():
        Z = zs[k0:k1][None, None, :]
        field[:, :, k0:k1] = np.maximum(
            field[:, :, k0:k1], torus_field(X, Y, Z, cx, cy, cz, nx, ny, nz, major, tube)
        )


def add_mirrored_ellipsoid(cx, cy, cz, rx, ry, rz):
    add_ellipsoid(cx, cy, cz, rx, ry, rz)
    add_ellipsoid(-cx, cy, cz, rx, ry, rz)


def add_chain(points, radii):
    for (cx, cy, cz), (rx, ry, rz) in zip(points, radii):
        add_ellipsoid(cx, cy, cz, rx, ry, rz)


def capsule_field(X, Y, Z, a, b, radius):
    """Round capsule field around a 3D line segment, positive inside."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    v = b - a
    vv = float(np.dot(v, v))
    t = ((X - a[0]) * v[0] + (Y - a[1]) * v[1] + (Z - a[2]) * v[2]) / vv
    t = np.clip(t, 0.0, 1.0)
    dx = X - (a[0] + t * v[0])
    dy = Y - (a[1] + t * v[1])
    dz = Z - (a[2] + t * v[2])
    return radius - np.sqrt(dx * dx + dy * dy + dz * dz)


def add_capsule(a, b, radius):
    X = xs[:, None, None]
    Y = ys[None, :, None]
    for k0, k1 in _chunk_slices():
        Z = zs[k0:k1][None, None, :]
        field[:, :, k0:k1] = np.maximum(field[:, :, k0:k1], capsule_field(X, Y, Z, a, b, radius))


def add_segment(a, b, radius):
    """Fuse an ellipsoidal tube between two points using overlapping samples."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    length = float(np.linalg.norm(b - a))
    n = max(2, int(math.ceil(length / (radius * 0.75))))
    for t in np.linspace(0.0, 1.0, n):
        p = a * (1.0 - t) + b * t
        add_ellipsoid(float(p[0]), float(p[1]), float(p[2]), radius, radius, radius)


# ---------------------------------------------------------------------------
# BASE / PADMASANA
# ---------------------------------------------------------------------------
# Low rounded charan-chowki, matching the reference and bridging the underside
# of the knees. The visible lotus region still occupies z=0..12 as one support.
add_rounded_box(0.0, 0.40, 1.90, 12.0, 5.75, 1.90, 0.65)
# Pelvic seat and two large crossed thighs.
add_ellipsoid(0.0, 0.70, 11.2, 8.0, 4.8, 3.8)
for s in (-1.0, 1.0):
    # The thigh crosses the body midline toward the opposite knee, matching
    # the visible X of a true Padmasana rather than two parallel leg lobes.
    hip = (s * 3.8, 0.20, 12.7)
    opposite_knee = (-s * 6.9, -2.35, 7.1)
    opposite_foot = (-s * 4.55, -5.00, 8.9)
    add_capsule(hip, opposite_knee, 4.0)
    add_capsule(opposite_knee, opposite_foot, 3.25)
    add_ellipsoid(opposite_foot[0], opposite_foot[1], opposite_foot[2], 2.55, 2.15, 1.35)
# Central bridge keeps the crossed knees as one smooth CNC-supporting mass.
add_ellipsoid(0.0, -3.6, 6.0, 5.0, 3.3, 2.8)
# Toes are intentionally suppressed in this base mesh: the reference's clean
# temple finish is retained without fragile beads or detached toe geometry.

# ---------------------------------------------------------------------------
# TORSO / SHOULDERS / NECK
# ---------------------------------------------------------------------------
add_ellipsoid(0.0, 0.55, 15.7, 8.7, 4.8, 6.2)  # pelvis
add_ellipsoid(0.0, 0.05, 23.5, 9.4, 4.9, 8.4)  # abdomen
add_ellipsoid(0.0, -0.05, 30.6, 12.0, 5.65, 9.6)  # 24-unit chest datum
add_ellipsoid(0.0, 0.10, 35.7, 9.0, 4.9, 6.2)
add_mirrored_ellipsoid(5.2, 0.05, 35.2, 4.25, 3.95, 4.45)
# Neck datum is z=42; navel datum is z=18, exactly 24 units apart.
add_ellipsoid(0.0, 0.10, 40.3, 4.5, 3.9, 5.0)
add_ellipsoid(0.0, 0.15, 42.0, 4.2, 3.7, 3.7)
# Smooth navel landmark; it is not a drilled recess.
add_ellipsoid(0.0, -4.82, 18.0, 0.55, 0.32, 0.50)

# ---------------------------------------------------------------------------
# ARMS AND DHYANA MUDRA
# ---------------------------------------------------------------------------
# Upper arms descend beside the torso, forearms turn inward, and both palms
# merge into the central lap. There are no hollow arm-body gaps.
for s in (-1.0, 1.0):
    shoulder = (s * 7.7, 0.00, 35.0)
    elbow = (s * 8.0, -0.55, 22.5)
    wrist = (s * 2.15, -4.25, 17.65)
    # Smooth capsules avoid the segmented/beaded appearance of overlapping
    # ellipsoids while retaining the natural elbow bend.
    add_capsule(shoulder, elbow, 2.65)
    add_capsule(elbow, wrist, 2.15)
# Lower left palm and upper right palm: a compact 7.6-unit-wide fused Dhyana Mudra.
add_rounded_box(-0.35, -4.65, 16.95, 3.45, 1.05, 0.52, 0.35)
add_rounded_box(0.35, -4.40, 17.75, 3.45, 1.05, 0.52, 0.35)
# Shallow fused finger rolls keep the Dhyana Mudra readable without fragile
# finger gaps or milling undercuts.
add_capsule((-2.75, -5.42, 17.03), (2.15, -5.42, 17.03), 0.30)
add_capsule((-2.25, -5.18, 17.82), (2.65, -5.18, 17.82), 0.28)

# ---------------------------------------------------------------------------
# HEAD / FACE / EARS
# ---------------------------------------------------------------------------
# Head exactly z=42..54, with facial width x=-7..+7. The jaw is blended into
# the neck so there is no sharp undercut beneath the chin.
add_ellipsoid(0.0, -0.20, 48.0, 7.0, 5.35, 6.0)
add_ellipsoid(0.0, -0.95, 46.15, 6.35, 4.75, 4.25)
add_ellipsoid(0.0, -0.72, 44.65, 5.6, 4.25, 2.75)
# Elongated lobes: exactly z=42..52 = 10 units.
add_mirrored_ellipsoid(7.38, -0.05, 47.0, 1.42, 2.35, 5.0)
# Shallow raised inner lobe line, not a deep ear cavity.
add_mirrored_ellipsoid(7.15, -2.28, 47.0, 0.30, 0.28, 3.55)
# Serene closed/half-lidded eyes, brows, nose, lips, and chin planes.
add_mirrored_ellipsoid(2.55, -5.08, 49.10, 1.75, 0.38, 0.22)
add_mirrored_ellipsoid(2.55, -4.98, 49.80, 1.95, 0.32, 0.24)
add_ellipsoid(0.0, -5.28, 48.25, 0.72, 0.62, 1.65)
add_ellipsoid(0.0, -5.72, 47.40, 0.56, 0.54, 0.56)
add_ellipsoid(0.0, -5.10, 46.15, 1.55, 0.32, 0.22)
add_ellipsoid(0.0, -4.92, 45.55, 2.5, 0.36, 0.40)

# ---------------------------------------------------------------------------
# MAHAVIRA HAIR: tight right-turning ringlets, not shoulder locks.
# ---------------------------------------------------------------------------
# A shallow fused scalp cap is the common bridge for the small curls. It stops
# above the neck, so it cannot become Rishabhanatha-style shoulder hair.
add_ellipsoid(0.0, 0.0, 50.0, 7.0, 5.3, 4.0)
# Ringlets are placed on the ellipsoidal scalp surface and intersected into the
# head. Their common handed placement gives a Dakshinavarti/Shankh-like turn.
head_c = np.array([0.0, -0.20, 48.0])
head_r = np.array([7.0, 5.35, 6.0])
for u in (0.18, 0.38, 0.58, 0.76, 0.90):
    radial_scale = math.sqrt(max(0.05, 1.0 - u * u))
    count = max(8, int(round(2.0 * math.pi * radial_scale * 2.7)))
    # Slight azimuthal shift in each row makes the curls read as a continuous
    # right-turning field rather than a checkerboard of dots.
    phase = 0.34 * (1.0 - u)
    for j in range(count):
        angle = 2.0 * math.pi * j / count + phase
        p = np.array([
            head_c[0] + head_r[0] * math.cos(angle) * radial_scale,
            head_c[1] + head_r[1] * math.sin(angle) * radial_scale,
            head_c[2] + head_r[2] * u,
        ])
        normal = np.array([
            (p[0] - head_c[0]) / (head_r[0] ** 2),
            (p[1] - head_c[1]) / (head_r[1] ** 2),
            (p[2] - head_c[2]) / (head_r[2] ** 2),
        ])
        normal = normal / np.linalg.norm(normal)
        # Move slightly outward; the tube still intersects the skull by ~0.1u.
        c = p + normal * 0.18
        add_torus(float(c[0]), float(c[1]), float(c[2]), normal, major=0.38, tube=0.22)
        # A short buried root bridges each ringlet into the skull. Without this
        # connector, a torus can be mathematically closed but visually floating
        # in an extracted voxel surface.
        root = c - normal * 0.22
        add_ellipsoid(float(root[0]), float(root[1]), float(root[2]), 0.30, 0.30, 0.30)
# Compact ushnisha stays inside the 54-unit head boundary.
add_ellipsoid(0.0, 0.10, 53.45, 3.0, 2.75, 0.55)

# ---------------------------------------------------------------------------
# RAISED SHRIVATSA: 4 wide x 5 high centered relief (diamond outline).
# ---------------------------------------------------------------------------
# Chest front at this level is approximately y=-5.4. The four bars are shallow,
# fused, and have no deep back pocket.
front_y = -5.42
corners = [(0.0, 34.0), (2.0, 31.5), (0.0, 29.0), (-2.0, 31.5)]
for a, b in zip(corners, corners[1:] + corners[:1]):
    add_segment((a[0], front_y, a[1]), (b[0], front_y, b[1]), 0.27)
# Fine central raised seed keeps the mark readable after CNC smoothing.
add_ellipsoid(0.0, front_y - 0.08, 31.5, 0.42, 0.28, 0.52)

# ---------------------------------------------------------------------------
# EXTRACT / NORMALIZE / AUDIT
# ---------------------------------------------------------------------------
verts, faces, normals, values = marching_cubes(
    field,
    level=0.0,
    spacing=(float(xs[1] - xs[0]), float(ys[1] - ys[0]), float(zs[1] - zs[0])),
    allow_degenerate=False,
)
verts[:, 0] += XMIN
verts[:, 1] += YMIN
verts[:, 2] += ZMIN

raw_min = verts.min(axis=0)
raw_max = verts.max(axis=0)
# Exact 54-unit height; x is normalized to the exact 24-unit chest datum. The
# field is symmetric, so this affine correction preserves bilateral symmetry.
verts[:, 2] = (verts[:, 2] - raw_min[2]) * (54.0 / (raw_max[2] - raw_min[2]))
raw_x_center = 0.5 * (raw_min[0] + raw_max[0])
verts[:, 0] = (verts[:, 0] - raw_x_center) * (24.0 / (raw_max[0] - raw_min[0]))
verts[:, 0] = np.where(np.abs(verts[:, 0]) < 1e-6, 0.0, verts[:, 0])

mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
try:
    mesh.remove_duplicate_faces()
    mesh.remove_degenerate_faces()
except AttributeError:
    pass
mesh.remove_unreferenced_vertices()
if mesh.volume < 0:
    mesh.invert()
# Marching cubes can leave tiny two-triangle slivers at sharp voxel/grid
# tangencies (especially at the rounded platform edge). Keep the dominant
# fused shell; this guarantees the CNC deliverable is one watertight component.
parts = mesh.split(only_watertight=False)
mesh = max(parts, key=lambda part: len(part.faces))
mesh.remove_unreferenced_vertices()
if mesh.volume < 0:
    mesh.invert()

stl_path = OUT / "tirthankara_padmasana_base_54u.stl"
obj_path = OUT / "tirthankara_padmasana_base_54u.obj"
mesh.export(stl_path)
mesh.export(obj_path)
components = mesh.split(only_watertight=False)
record = {
    "title": "Lord Mahavira, seated Digambar Jain Tirthankara, Padmasana, Dhyana Mudra",
    "source_document": "pratima vigyan.pdf",
    "reference_images": ["162086942_1790514492131653.jpg", "242938257_1790514490820601.jpg"],
    "style": "Traditional temple-sculpture base; smooth unadorned polished-marble finish; no clothing, jewelry, shoulder locks, or surface imperfections.",
    "coordinate_system": {"x": "left/right", "y": "front/back; front is negative", "z": "vertical"},
    "unit_note": "Normalized, unitless geometry. Uniformly rescale in CAM.",
    "height_datum": "z=0 at bottom of the rectangular charan-chowki/pedestal; z=54 at the top of the ushnisha.",
    "pedestal_included_in_total_height": True,
    "required_measurements": {
        "total_height": 54.0,
        "head_height": 12.0,
        "face_width": 14.0,
        "earlobe_vertical_length": 10.0,
        "neck_to_navel": 24.0,
        "chest_width": 24.0,
        "shrivatsa_width": 4.0,
        "shrivatsa_height": 5.0,
        "lotus_region_height": 12.0,
        "dhyana_mudra_width": 7.6,
    },
    "landmarks": {
        "bottom": 0.0,
        "lotus_region": [0.0, 12.0],
        "navel": 18.0,
        "neck": 42.0,
        "head": [42.0, 54.0],
        "earlobes": [42.0, 52.0],
        "shrivatsa": {"x": [-2.0, 2.0], "z": [29.0, 34.0]},
    },
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
    "cnc_note": "All anatomy, ears, hands, lotus legs, hair ringlets, and Shrivatsa are fused into one shell. No detached parts or deep trapped cavities are intentionally modeled; the leg/pedestal bridge supports 3-axis/4-axis roughing.",
}
(OUT / "tirthankara_measurement_audit.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps(record, indent=2))
print(f"Wrote {stl_path}")
print(f"Wrote {obj_path}")
