# GitHub Pages deployment

The viewer is already configured for a project-page URL such as:

```text
https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY-NAME/
```

The Vite base path is relative, so the STL loads correctly when the site is hosted below the domain root.

## Option A — push with Git

From the `tirthankara_mesh` folder:

```bash
git init
git branch -M main
git add .
git commit -m "Add Tirthankara 3D viewer"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY-NAME.git
git push -u origin main
```

If the repository already has a remote, use that remote instead of `git remote add origin`.

## Option B — upload in the GitHub website

Upload the **contents of this `tirthankara_mesh` folder**, including:

- `.github/workflows/deploy-pages.yml`
- `viewer/`
- the mesh/source files

Do not upload `viewer/node_modules/`; it is excluded by `.gitignore` and GitHub Actions installs the dependencies automatically.

## Enable Pages

1. Open the GitHub repository.
2. Go to **Settings → Pages**.
3. Under **Build and deployment → Source**, select **GitHub Actions**.
4. Open the **Actions** tab and wait for **Deploy 3D viewer to GitHub Pages** to finish.
5. GitHub will show the live URL in the workflow's deployment environment.

The first deployment normally takes a minute or two. The 18 MB STL is below GitHub's regular per-file upload limit, so Git LFS is not required for this mesh.

## Test the production build locally

```bash
cd viewer
npm ci
npm run build
npm run preview -- --host 0.0.0.0
```

The production output is written to `viewer/dist/` and is exactly what the Pages workflow publishes.
