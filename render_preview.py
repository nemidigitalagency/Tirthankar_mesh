from pathlib import Path
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parent
mesh = trimesh.load_mesh(ROOT / 'output/tirthankara_padmasana_base_54u.stl', process=False)
# Keep the complete shell for a solid inspection render. Matplotlib handles
# this resolution in a few seconds and avoids a dotted decimated preview.
tri = mesh.triangles

fig = plt.figure(figsize=(12, 7), dpi=160, facecolor='#f4f1e9')
for idx, (elev, azim, title) in enumerate([(8, 0, 'FRONT'), (14, -28, 'THREE-QUARTER')], 1):
    ax = fig.add_subplot(1, 2, idx, projection='3d')
    poly = Poly3DCollection(tri, linewidths=0.0, alpha=1.0)
    poly.set_facecolor('#b58a55')
    poly.set_edgecolor('none')
    ax.add_collection3d(poly)
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlim(-14, 14); ax.set_ylim(-10, 9); ax.set_zlim(0, 54)
    ax.set_box_aspect((28, 19, 54))
    ax.set_axis_off()
    ax.set_title(title, fontsize=12, fontweight='bold', pad=8, color='#3c3327')
fig.suptitle('Digambar Jain Tirthankara — Padmasana base mesh | normalized height 54 units', fontsize=14, fontweight='bold', color='#3c3327', y=0.96)
fig.text(0.5, 0.035, 'Single watertight implicit-union shell • no separate overlapping shells • front is y negative', ha='center', fontsize=9, color='#5c5145')
fig.savefig(ROOT / 'tirthankara_padmasana_preview.png', bbox_inches='tight', facecolor=fig.get_facecolor())
print('saved preview')
