from pathlib import Path
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import to_rgb

ROOT = Path(__file__).resolve().parent
mesh = trimesh.load_mesh(ROOT / 'output/tirthankara_padmasana_base_54u.obj', process=True)
# Decimate only the inspection render; the STL/OBJ deliverables remain full
# resolution. The decimated shell stays closed and makes matplotlib responsive.
mesh = mesh.simplify_quadric_decimation(face_count=45000)
tri = mesh.triangles

# Simple marble studio shading: matplotlib's 3D collection does not apply
# physically based light by itself, so shade each triangle from its normal.
base = np.array(to_rgb('#d7d0c4'))
light = np.array([-0.30, -0.78, 0.58], dtype=float)
light /= np.linalg.norm(light)
intensity = 0.38 + 0.62 * np.clip(mesh.face_normals.dot(light), 0.0, 1.0)
face_colors = np.clip(base[None, :] * intensity[:, None], 0, 1)

fig = plt.figure(figsize=(12, 7), dpi=160, facecolor='#f4f1e9')
for idx, (elev, azim, title) in enumerate([(8, -90, 'FRONT'), (14, -55, 'THREE-QUARTER')], 1):
    ax = fig.add_subplot(1, 2, idx, projection='3d')
    poly = Poly3DCollection(tri, linewidths=0.0, alpha=1.0)
    poly.set_facecolors(face_colors)
    poly.set_edgecolor('none')
    ax.add_collection3d(poly)
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlim(-14, 14); ax.set_ylim(-10, 9); ax.set_zlim(0, 54)
    ax.set_box_aspect((28, 19, 54))
    ax.set_axis_off()
    ax.set_title(title, fontsize=12, fontweight='bold', pad=8, color='#3c3327')
fig.suptitle('Lord Mahavira — Digambar Jain Tirthankara | Padmasana base mesh | normalized height 54 units', fontsize=14, fontweight='bold', color='#3c3327', y=0.96)
fig.text(0.5, 0.035, 'Single watertight shell • Dhyana Mudra • fused CNC-friendly anatomy • front is y negative', ha='center', fontsize=9, color='#5c5145')
fig.savefig(ROOT / 'tirthankara_padmasana_preview.png', bbox_inches='tight', facecolor=fig.get_facecolor())
print('saved preview')
