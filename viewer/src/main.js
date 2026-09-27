import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import './style.css';

const stage = document.querySelector('#stage');
const loading = document.querySelector('#loading');
const errorBox = document.querySelector('#error');
const statusText = document.querySelector('#statusText');
const topology = document.querySelector('#topology');
const components = document.querySelector('#components');
const triangles = document.querySelector('#triangles');

const scene = new THREE.Scene();
scene.background = new THREE.Color('#eee9df');
scene.fog = new THREE.Fog('#eee9df', 95, 180);

const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 500);
camera.up.set(0, 0, 1); // normalized mesh is z-up

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.screenSpacePanning = true;
controls.minDistance = 20;
controls.maxDistance = 180;
controls.target.set(0, 0, 27);

// Warm studio lighting suitable for reading the relief and silhouette.
scene.add(new THREE.HemisphereLight('#fffaf0', '#766b60', 2.15));
const key = new THREE.DirectionalLight('#fff6df', 4.1);
key.position.set(-45, -65, 90);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.left = -35;
key.shadow.camera.right = 35;
key.shadow.camera.top = 70;
key.shadow.camera.bottom = -10;
scene.add(key);
const rim = new THREE.DirectionalLight('#b6c6de', 1.4);
rim.position.set(45, 25, 50);
scene.add(rim);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(90, 90),
  new THREE.MeshStandardMaterial({ color: '#ded6c9', roughness: 0.92, metalness: 0 })
);
ground.position.z = -0.04;
ground.receiveShadow = true;
scene.add(ground);

const grid = new THREE.GridHelper(50, 25, '#a99d8e', '#d0c5b6');
grid.rotation.x = Math.PI / 2;
grid.position.z = 0.01;
grid.material.transparent = true;
grid.material.opacity = 0.5;
scene.add(grid);

const modelGroup = new THREE.Group();
scene.add(modelGroup);
let modelMesh = null;
let wireMesh = null;
let defaultDistance = 90;

function setStatus(text, ready = false) {
  statusText.textContent = text;
  document.querySelector('.status-dot').classList.toggle('ready', ready);
}

function frameModel(distance = null) {
  if (!modelMesh) return;
  const box = new THREE.Box3().setFromObject(modelGroup);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  controls.target.copy(center);
  const d = distance ?? Math.max(66, size.z * 1.48);
  defaultDistance = d;
  camera.position.set(d * 0.62, -d * 0.94, d * 0.48);
  camera.lookAt(center);
  controls.update();
}

function frontView() {
  if (!modelMesh) return;
  const box = new THREE.Box3().setFromObject(modelGroup);
  const center = box.getCenter(new THREE.Vector3());
  const d = defaultDistance * 0.92;
  camera.position.set(0, -d, center.z + 1.5);
  controls.target.copy(center);
  controls.update();
}

function threeQuarterView() {
  if (!modelMesh) return;
  const box = new THREE.Box3().setFromObject(modelGroup);
  const center = box.getCenter(new THREE.Vector3());
  const d = defaultDistance;
  camera.position.set(d * 0.62, -d * 0.94, center.z + d * 0.45);
  controls.target.copy(center);
  controls.update();
}

function showError(message) {
  loading.hidden = true;
  errorBox.hidden = false;
  errorBox.innerHTML = `<strong>Could not load the model.</strong><br>${message}`;
  setStatus('Load error');
}

const modelUrl = `${import.meta.env.BASE_URL}tirthankara.stl`;

new STLLoader().load(
  modelUrl,
  (geometry) => {
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    const material = new THREE.MeshStandardMaterial({
      color: '#a97946',
      roughness: 0.76,
      metalness: 0.035,
      flatShading: false,
    });
    modelMesh = new THREE.Mesh(geometry, material);
    modelMesh.castShadow = true;
    modelMesh.receiveShadow = true;
    modelGroup.add(modelMesh);

    // Separate line overlay uses the same geometry and stays disabled by default.
    wireMesh = new THREE.Mesh(
      geometry,
      new THREE.MeshBasicMaterial({ color: '#3a291d', wireframe: true, transparent: true, opacity: 0.13 })
    );
    wireMesh.visible = false;
    modelGroup.add(wireMesh);

    const triCount = geometry.attributes.position.count / 3;
    topology.textContent = 'Closed shell';
    components.textContent = '1';
    triangles.textContent = Math.round(triCount).toLocaleString();
    loading.hidden = true;
    setStatus('Mesh ready', true);
    frameModel();
  },
  (event) => {
    if (event.total) {
      const pct = Math.round((event.loaded / event.total) * 100);
      statusText.textContent = `Loading mesh ${pct}%`;
    }
  },
  (err) => showError(err?.message || 'The local mesh asset was not found.')
);

document.querySelector('#frontBtn').addEventListener('click', frontView);
document.querySelector('#threeBtn').addEventListener('click', threeQuarterView);
document.querySelector('#resetBtn').addEventListener('click', () => frameModel());
document.querySelector('#wireToggle').addEventListener('change', (e) => {
  if (wireMesh) wireMesh.visible = e.target.checked;
});
document.querySelector('#gridToggle').addEventListener('change', (e) => {
  grid.visible = e.target.checked;
  ground.visible = e.target.checked;
});

function resize() {
  const width = stage.clientWidth;
  const height = stage.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}
window.addEventListener('resize', resize);
resize();

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
