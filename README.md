# Lord Mahavira — Digambar Jain Tirthankara, Padmasana base mesh

Generated from the attached **`pratima vigyan.pdf`** and the supplied front/side reference images. This revision is a symmetrical, normalized CNC base of Lord Mahavira in seated Padmasana with Dhyana Mudra, intended for further sculpting or CNC/CAM preparation.

## Files

- `output/tirthankara_padmasana_base_54u.stl` — primary watertight mesh for CAM/slicing.
- `output/tirthankara_padmasana_base_54u.obj` — editable OBJ copy with the same coordinates.
- `output/tirthankara_measurement_audit.json` — dimensions, landmark levels, and topology audit.
- `create_tirthankara.py` — reproducible parametric generator.
- `tirthankara_padmasana_preview.png` — front and three-quarter inspection preview.

## Master proportions

The model uses the prompt's 54-unit scheme as the controlling datum:

- Total height: **54 units**, z = 0 to 54.
- Head: **12 units**, z = 42 to 54.
- Main face: **14 units wide**.
- Elongated earlobes: **10 units vertically**, z = 42 to 52.
- Neck landmark to navel: **24 units**, neck z = 42, navel z = 18.
- Chest: **24 units wide**, normalized to x = -12 to +12.
- Raised central Shrivatsa envelope: **4 wide × 5 high**, x = -2..+2 and z = 29..34.
- Folded Padmasana leg mass: **bottom 12 units**, z = 0 to 12.

The PDF contains several traditional measurement columns with variations. The explicit master values above were therefore used where the request called them crucial; the remaining body is a smooth, stylized CNC-ready base rather than a fully detailed final carving.

## Mesh properties

The mesh is generated as one implicit union and exported as one closed shell. The final audit reports:

- Watertight: **true**
- Winding consistent: **true**
- Connected components: **1**
- 184,154 vertices / 368,304 triangles
- No open boundaries, internal overlapping STL shells, or through-holes
- Arms, chin/neck, and crossed legs are blended into continuous volumes; the Shrivatsa is a shallow fused relief

## Units and CAM

STL and OBJ do not carry a universal unit declaration. The supplied mesh is normalized and unitless. In the CAM package, set **1 mesh unit** to the desired shop unit, or scale uniformly to the finished height. For example, to make the figure 540 mm tall, scale by 10 mm per unit.

## GitHub Pages viewer

A Vite + Three.js viewer is included in `viewer/`. The repository contains a GitHub Actions workflow at `.github/workflows/deploy-pages.yml`; push the contents of this folder to a GitHub repository, enable **Settings → Pages → GitHub Actions**, and the interactive viewer will publish at `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/`. See `GITHUB_PAGES_DEPLOY.md` for the exact commands.
