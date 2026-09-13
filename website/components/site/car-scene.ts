import * as THREE from "three";
import type { StepId } from "@/lib/detail-steps";

// A car built in code: nothing to download and no model licence to worry about.
// One custom shader carries the whole detail. Each stage is a set of uniforms the
// render loop drives: foam pouring down, a wash front sweeping along the panels,
// clay lifting bonded specks, iron bleeding purple, then the coating going glossy
// and pulling water into beads.
//
// Object space is the car's own space: x runs nose (-2.5) to tail (+2.5), y runs
// from under the sills (0.08) to the roof (1.52), z is the width. Every effect
// below is written in those numbers.

export type CarScene = {
  setStep: (id: StepId) => void;
  setActive: (on: boolean) => void;
  dispose: () => void;
};

type Opts = { reduced: boolean; lowPower: boolean };

const clamp01 = (n: number) => (n < 0 ? 0 : n > 1 ? 1 : n);
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const mix = (a: number, b: number, t: number) => a + (b - a) * t;

// ---------------------------------------------------------------- car geometry

// The side view, traced off a straight-on photo of a real coupe and kept to its
// actual proportions: 4.79 long, 1.34 tall, 2.86 between the axles. Extruded
// across the width, with a bevel that rounds every edge.
function bodyProfile() {
  const s = new THREE.Shape();
  s.moveTo(-2.38, 0.34); // nose, low
  s.lineTo(-1.95, 0.2); // under the front bumper
  s.quadraticCurveTo(-1.46, 1.4, -0.97, 0.2); // front arch, peaking at 0.80
  s.lineTo(0.9, 0.16); // side skirt
  s.quadraticCurveTo(1.4, 1.36, 1.89, 0.2); // rear arch
  s.lineTo(2.34, 0.26);
  s.quadraticCurveTo(2.42, 0.5, 2.4, 0.82); // tail face
  s.quadraticCurveTo(2.36, 0.98, 2.24, 1.0); // ducktail lip
  s.lineTo(2.12, 0.96);
  s.lineTo(1.66, 1.01); // boot lid
  s.quadraticCurveTo(1.28, 1.18, 0.94, 1.29); // rear screen
  s.lineTo(0.12, 1.34); // roof
  s.quadraticCurveTo(-0.24, 1.3, -0.44, 1.14);
  s.quadraticCurveTo(-0.58, 1.02, -0.78, 0.96); // windscreen into the cowl
  s.lineTo(-1.5, 0.84); // bonnet
  s.quadraticCurveTo(-2.06, 0.74, -2.26, 0.63);
  s.quadraticCurveTo(-2.44, 0.52, -2.38, 0.34); // nose
  return s;
}

const smoothstep = (a: number, b: number, x: number) => {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

function buildBody(material: THREE.Material, lowPower: boolean) {
  const depth = 1.63;
  const geo = new THREE.ExtrudeGeometry(bodyProfile(), {
    depth,
    bevelEnabled: true,
    bevelThickness: 0.15,
    bevelSize: 0.13,
    bevelOffset: 0,
    bevelSegments: lowPower ? 4 : 7,
    curveSegments: lowPower ? 14 : 24,
  });
  // Centre the width only. Leaving x and y alone keeps object space readable.
  geo.translate(0, 0, -depth / 2);

  // A straight extrusion is a bar of soap. Squeezing the width by height and by
  // length is what gives it a cabin that sits inside the shoulders, a nose that
  // narrows, and sills that tuck under.
  const pos = geo.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const z = pos.getZ(i);
    // Only the greenhouse narrows. Squeezing purely by height would pinch the
    // bonnet and the boot too, which is what turns a coupe into a ute.
    const greenhouse = smoothstep(-1.05, -0.62, x) * (1 - smoothstep(1.5, 1.9, x));
    const cabin = 1 - 0.44 * smoothstep(0.92, 1.22, y) * greenhouse;
    const nose = 1 - 0.26 * smoothstep(1.7, 2.45, -x); // the front tapers hard
    const tail = 1 - 0.1 * smoothstep(2.0, 2.45, x); // the rear stays broad
    const sill = 1 - 0.14 * smoothstep(0.42, 0.14, y); // skirts tuck under
    pos.setZ(i, z * cabin * nose * tail * sill);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, material);
}

function buildWheel(lowPower: boolean) {
  const g = new THREE.Group();
  const seg = lowPower ? 18 : 32;

  const tyre = new THREE.Mesh(
    new THREE.CylinderGeometry(0.36, 0.36, 0.34, seg),
    new THREE.MeshPhysicalMaterial({ color: 0x0a0b0d, roughness: 0.8, metalness: 0, clearcoat: 0.2 }),
  );
  tyre.rotation.x = Math.PI / 2;
  g.add(tyre);

  const rim = new THREE.Mesh(
    new THREE.CylinderGeometry(0.25, 0.25, 0.36, seg),
    new THREE.MeshPhysicalMaterial({ color: 0x9099a6, roughness: 0.22, metalness: 1 }),
  );
  rim.rotation.x = Math.PI / 2;
  g.add(rim);

  // Five spokes, just enough to catch the light as the car turns.
  const spokeMat = new THREE.MeshPhysicalMaterial({ color: 0x9aa4b2, roughness: 0.19, metalness: 1 });
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.22, 0.36), spokeMat);
    spoke.position.set(Math.cos(a) * 0.11, Math.sin(a) * 0.11, 0);
    spoke.rotation.z = a;
    g.add(spoke);
  }

  const disc = new THREE.Mesh(
    new THREE.CylinderGeometry(0.16, 0.16, 0.07, seg),
    new THREE.MeshPhysicalMaterial({ color: 0x262b31, roughness: 0.5, metalness: 0.9 }),
  );
  disc.rotation.x = Math.PI / 2;
  g.add(disc);
  return g;
}

// A soft dark patch under the car so it sits on the ground instead of floating.
function groundShadow() {
  const size = 256;
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const ctx = c.getContext("2d")!;
  const grad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, "rgba(0,0,0,0.75)");
  grad.addColorStop(0.42, "rgba(0,0,0,0.36)");
  grad.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(c);
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(7.6, 3.4),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }),
  );
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = 0.004;
  return mesh;
}

// A studio in a box: bright strips overhead and behind, brand blue down the flanks.
// Those long highlights sliding across the panels are what make paint read as paint.
function studioEnvironment(renderer: THREE.WebGLRenderer) {
  const env = new THREE.Scene();
  env.background = new THREE.Color(0x04060a);
  const strip = (w: number, h: number, colour: number, pos: [number, number, number], power = 1) => {
    // Brighter than white on purpose: these are the lights, not lit surfaces.
    const c = new THREE.Color(colour).multiplyScalar(power);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: c }));
    m.position.set(...pos);
    m.lookAt(0, 0, 0);
    env.add(m);
  };
  strip(15, 1.5, 0xffffff, [0, 7, 1.8], 9);
  strip(12, 1.1, 0xe6eef8, [0, 6.4, -3.4], 5);
  strip(11, 1, 0xdbe6f4, [0, 5.6, 5.2], 4);
  strip(3.2, 7.5, 0x4b9ae8, [-7.5, 2.4, 1.2], 4.5);
  strip(3.2, 7.5, 0x2f74bd, [7.5, 2.4, -1.2], 3);
  strip(9, 2.2, 0x9db2cc, [0, 1.6, -9], 2);
  strip(16, 5, 0x0b1017, [0, -6, 0], 1);

  const pmrem = new THREE.PMREMGenerator(renderer);
  const target = pmrem.fromScene(env, 0.08);
  pmrem.dispose();
  env.traverse((o) => {
    if (o instanceof THREE.Mesh) {
      o.geometry.dispose();
      (o.material as THREE.Material).dispose();
    }
  });
  return target.texture;
}

// ---------------------------------------------------------------- body shader

const NOISE = /* glsl */ `
float hash31(vec3 p){ p = fract(p * 0.3183099 + vec3(0.71, 0.113, 0.419)); p *= 17.0;
  return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float vnoise(vec3 x){
  vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash31(i), hash31(i + vec3(1,0,0)), f.x),
                 mix(hash31(i + vec3(0,1,0)), hash31(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash31(i + vec3(0,0,1)), hash31(i + vec3(1,0,1)), f.x),
                 mix(hash31(i + vec3(0,1,1)), hash31(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float fbm(vec3 p){ float s = 0.0; float a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * vnoise(p); p *= 2.03; a *= 0.5; } return s; }
`;

type Uniforms = Record<string, THREE.IUniform<number>>;

function paintMaterial(): { material: THREE.MeshPhysicalMaterial; uniforms: Uniforms } {
  const uniforms: Uniforms = {
    uTime: { value: 0 },
    uDirt: { value: 0 },
    uWashX: { value: -3.4 },
    uFoam: { value: 0 },
    uFoamFade: { value: 1 },
    uSpeck: { value: 0 },
    uClayX: { value: -3.4 },
    uIron: { value: 0 },
    uIronRun: { value: 1.7 },
    uGloss: { value: 0 },
    uBeads: { value: 0 },
  };

  const material = new THREE.MeshPhysicalMaterial({
    color: 0x11694b,
    metalness: 0.62,
    roughness: 0.24,
    clearcoat: 0.55,
    clearcoatRoughness: 0.1,
    envMapIntensity: 1.5,
  });

  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);

    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", `#include <common>\nvarying vec3 vObj;`)
      .replace("#include <begin_vertex>", `#include <begin_vertex>\nvObj = position;`);

    shader.fragmentShader = shader.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>
varying vec3 vObj;
uniform float uTime, uDirt, uWashX, uFoam, uFoamFade, uSpeck, uClayX, uIron, uIronRun, uGloss, uBeads;
${NOISE}
// Scratch values handed from the colour pass down to the roughness and normal passes.
float sDirt; float sFoam; float sSpeck; float sGlass; float sBead; vec3 sBeadDir;
float glassMask(vec3 p){
  return smoothstep(0.97, 1.08, p.y)
       * smoothstep(-0.82, -0.56, p.x)
       * (1.0 - smoothstep(1.5, 1.76, p.x));
}`,
      )
      .replace(
        "#include <color_fragment>",
        `#include <color_fragment>
{
  vec3 P = vObj;
  float glass = glassMask(P);

  // Windows: darker than the paint, and they stay sharper than it too.
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.012, 0.017, 0.025), glass * 0.93);

  // Road grime: patchy, and always worst down low.
  float low = 1.0 - smoothstep(0.28, 1.0, P.y);
  float grime = fbm(P * 2.4) * 0.72 + 0.32;
  float dirt = uDirt * smoothstep(uWashX - 0.3, uWashX + 0.06, P.x) * grime * mix(0.48, 1.0, low);
  dirt = clamp(dirt, 0.0, 1.0);
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.21, 0.19, 0.165), dirt * 0.86);

  // Bonded contamination: what you feel before you can see it.
  float speckHash = hash31(floor(P * 78.0));
  float specks = step(0.975, speckHash) * uSpeck * smoothstep(uClayX - 0.24, uClayX + 0.05, P.x);
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.13, 0.115, 0.1), specks);

  // Iron remover going off: violet, and it runs downhill as it works.
  float streak = fbm(vec3(P.x * 13.0, P.y * 0.8 - uTime * 0.16, P.z * 13.0));
  float run = smoothstep(0.36, 0.62, streak);
  float reach = smoothstep(uIronRun - 0.3, uIronRun + 0.16, P.y);
  float ironAmt = clamp(uIron * run * mix(0.6, 1.0, low) * reach, 0.0, 1.0);
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.29, 0.015, 0.2), ironAmt * 0.88);

  // Snow foam pouring down over the lot.
  float foamLine = mix(1.68, -0.25, uFoam);
  float fn = fbm(P * 3.4 + vec3(0.0, -uTime * 0.15, 0.0));
  float foam = clamp(smoothstep(foamLine - 0.32, foamLine + 0.1, P.y + (fn - 0.5) * 0.6) * uFoamFade, 0.0, 1.0);
  float bubbles = smoothstep(0.42, 0.74, fbm(P * 17.0)) * 0.13;
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.9, 0.93, 0.965) - bubbles, foam * 0.95);

  // The wet edge that follows the mitt down the panel.
  float edge = exp(-pow((P.x - uWashX) / 0.22, 2.0)) * uDirt;
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.85, 0.89, 0.94), edge * 0.45);

  sDirt = dirt; sFoam = foam; sSpeck = specks; sGlass = glass;
}`,
      )
      .replace(
        "#include <roughnessmap_fragment>",
        `#include <roughnessmap_fragment>
{
  roughnessFactor = mix(roughnessFactor, 0.1, uGloss);
  roughnessFactor = mix(roughnessFactor, 0.6, sSpeck);
  roughnessFactor = mix(roughnessFactor, 0.95, sDirt);
  roughnessFactor = mix(roughnessFactor, 0.88, sFoam);
  roughnessFactor = mix(roughnessFactor, 0.05, sGlass * 0.9);

  // Water standing on a sealed panel, pulled up into beads.
  vec3 bp = vObj * 15.0;
  vec3 cellId = floor(bp);
  vec3 cellF = fract(bp) - 0.5;
  float r = hash31(cellId);
  float d = length(cellF) * (0.55 + r * 0.8);
  sBead = smoothstep(0.32, 0.08, d) * step(0.56, r) * uBeads;
  sBeadDir = cellF;
  roughnessFactor = mix(roughnessFactor, 0.02, sBead);
}`,
      )
      .replace(
        "#include <normal_fragment_maps>",
        `#include <normal_fragment_maps>
normal = normalize(normal + normalize(vec3(sBeadDir.x, sBeadDir.z, sBeadDir.y) + 0.001) * sBead * 1.9);`,
      );
  };

  return { material, uniforms };
}

// ---------------------------------------------------------------------- scene

export function createCarScene(canvas: HTMLCanvasElement, opts: Opts): CarScene {
  const { reduced, lowPower } = opts;

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: !lowPower,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, lowPower ? 1.3 : 1.7));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.32;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 60);
  camera.position.set(6, 2.6, 6);

  const envTexture = studioEnvironment(renderer);
  scene.environment = envTexture;

  const { material: paint, uniforms } = paintMaterial();
  const car = new THREE.Group();
  car.add(buildBody(paint, lowPower));

  for (const [x, z] of [
    [-1.46, 0.76],
    [-1.46, -0.76],
    [1.4, 0.76],
    [1.4, -0.76],
  ]) {
    const wheel = buildWheel(lowPower);
    wheel.position.set(x, 0.36, z);
    car.add(wheel);
  }
  scene.add(car);
  scene.add(groundShadow());

  const key = new THREE.DirectionalLight(0xffffff, 2.1);
  key.position.set(4, 7, 5);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x63a8ee, 2.4);
  rim.position.set(-6, 3, -5);
  scene.add(rim);
  const fill = new THREE.DirectionalLight(0xbfd4ee, 0.9);
  fill.position.set(2, 2, -6);
  scene.add(fill);
  scene.add(new THREE.AmbientLight(0x44546b, 1.1));

  // ------------------------------------------------------------- interaction

  let azimuth = 0.75;
  let elevation = 0.22;
  let targetAz = azimuth;
  let targetEl = elevation;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let idleSince = performance.now();

  const onDown = (e: PointerEvent) => {
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  };
  const onMove = (e: PointerEvent) => {
    if (!dragging) return;
    targetAz -= (e.clientX - lastX) * 0.007;
    targetEl = Math.max(0.02, Math.min(0.6, targetEl - (e.clientY - lastY) * 0.004));
    lastX = e.clientX;
    lastY = e.clientY;
    idleSince = performance.now();
  };
  const onUp = (e: PointerEvent) => {
    dragging = false;
    idleSince = performance.now();
    if (canvas.hasPointerCapture(e.pointerId)) canvas.releasePointerCapture(e.pointerId);
  };
  canvas.addEventListener("pointerdown", onDown);
  canvas.addEventListener("pointermove", onMove);
  canvas.addEventListener("pointerup", onUp);
  canvas.addEventListener("pointercancel", onUp);

  // ---------------------------------------------------------------- stepping

  let step: StepId = "foam";
  let stepStart = 0;
  let clock = 0;

  const setStep = (id: StepId) => {
    step = id;
    stepStart = clock;
  };

  function driveUniforms(t: number) {
    const u = uniforms;
    // Reduced motion gets each stage's finished state, with nothing moving.
    const at = (dur: number, delay = 0, ease = easeOut) => (reduced ? 1 : ease(clamp01((t - delay) / dur)));

    u.uTime.value = reduced ? 0 : clock;
    u.uDirt.value = 0;
    u.uWashX.value = -3.4;
    u.uFoam.value = 0;
    u.uFoamFade.value = 1;
    u.uSpeck.value = 0;
    u.uClayX.value = -3.4;
    u.uIron.value = 0;
    u.uIronRun.value = 1.7;
    u.uGloss.value = 0;
    u.uBeads.value = 0;
    paint.clearcoat = 0.5;
    paint.envMapIntensity = 1.5;

    if (step === "foam") {
      u.uDirt.value = 1;
      u.uFoam.value = at(2.4);
    } else if (step === "wash") {
      u.uDirt.value = 1;
      u.uFoam.value = 1;
      u.uFoamFade.value = 1 - at(1.1, 0, easeInOut);
      u.uWashX.value = mix(-3.4, 3.4, at(2.8, 0.7, easeInOut));
    } else if (step === "clay") {
      u.uSpeck.value = 1;
      const sweep = at(3, 0.4, easeInOut);
      u.uClayX.value = mix(-3.4, 3.4, sweep);
      u.uGloss.value = sweep * 0.4;
    } else if (step === "iron") {
      u.uIron.value = at(1.2);
      u.uIronRun.value = mix(1.7, -0.35, at(3.4, 0.3));
    } else if (step === "coat") {
      const g = at(1.8);
      u.uGloss.value = g;
      u.uBeads.value = at(2.2, 1.1);
      paint.clearcoat = mix(0.5, 1, g);
      paint.envMapIntensity = mix(1.5, 2.3, g);
    }
  }

  // ------------------------------------------------------------------- loop

  let active = true;
  let raf = 0;
  let last = performance.now();
  let width = 1;
  let height = 1;

  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(rect.width));
    const h = Math.max(1, Math.round(rect.height));
    if (w === width && h === height) return;
    width = w;
    height = h;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };

  const ro = new ResizeObserver(resize);
  ro.observe(canvas);

  const frame = (now: number) => {
    raf = requestAnimationFrame(frame);
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (!active) return;
    clock += dt;
    resize();

    if (!reduced && !dragging && now - idleSince > 2200) targetAz += dt * 0.12;
    const k = reduced ? 1 : 0.09;
    azimuth += (targetAz - azimuth) * k;
    elevation += (targetEl - elevation) * k;

    // Narrow screens need a little more room to keep the whole car in frame.
    const dist = width / height < 1.15 ? 8.2 : 7.1;
    camera.position.set(
      Math.sin(azimuth) * Math.cos(elevation) * dist,
      0.9 + Math.sin(elevation) * dist,
      Math.cos(azimuth) * Math.cos(elevation) * dist,
    );
    camera.lookAt(0, 0.66, 0);

    driveUniforms(clock - stepStart);
    renderer.render(scene, camera);
  };

  resize();
  raf = requestAnimationFrame(frame);

  return {
    setStep,
    setActive: (on: boolean) => {
      active = on;
      if (on) last = performance.now();
    },
    dispose: () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener("pointerdown", onDown);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerup", onUp);
      canvas.removeEventListener("pointercancel", onUp);
      scene.traverse((o) => {
        if (o instanceof THREE.Mesh) {
          o.geometry.dispose();
          const m = o.material;
          if (Array.isArray(m)) m.forEach((x) => x.dispose());
          else m.dispose();
        }
      });
      envTexture.dispose();
      renderer.dispose();
    },
  };
}
