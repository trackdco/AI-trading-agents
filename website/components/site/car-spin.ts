import type { StepId } from "@/lib/detail-steps";

// The real car, spun by stepping through frames cut from one orbit, with each
// stage of the detail painted on in a fragment shader. No 3D engine: it is a
// single quad, one texture, and a lot of noise maths.
//
// In the shader, u runs nose to tail across the frame and v runs from the ground
// (0) to above the roof (1). Every stage below is written in those terms.

export type CarSpin = {
  setStep: (id: StepId) => void;
  setActive: (on: boolean) => void;
  dispose: () => void;
};

type Opts = { reduced: boolean; lowPower: boolean; onReady: () => void };

const clamp01 = (n: number) => (n < 0 ? 0 : n > 1 ? 1 : n);
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const mix = (a: number, b: number, t: number) => a + (b - a) * t;

const VERT = `#version 300 es
in vec2 aPos;
out vec2 vUv;
void main(){ vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;

const FRAG = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 outColor;
uniform sampler2D uTex;
uniform float uTime, uDirt, uWashX, uFoam, uFoamFade, uSpeck, uClayX, uIron, uIronRun, uGloss, uBeads, uSpin;

float hash21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){
  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash21(i), hash21(i + vec2(1,0)), f.x),
             mix(hash21(i + vec2(0,1)), hash21(i + vec2(1,1)), f.x), f.y);
}
float fbm(vec2 p){ float s = 0.0, a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * vnoise(p); p *= 2.03; a *= 0.5; } return s; }

void main(){
  vec4 t = texture(uTex, vUv);
  float car = t.a;

  // Outside the car is the studio it was shot in, pulled down onto the site's
  // palette so the panel sits in the page instead of glowing out of it.
  float bgl = dot(t.rgb, vec3(0.299, 0.587, 0.114));
  vec3 bg = mix(vec3(0.028, 0.042, 0.062), vec3(0.115, 0.155, 0.205), bgl);
  vec2 q = vUv - 0.5;
  bg *= 1.0 - 1.15 * dot(q, q);
  if (car < 0.004) { outColor = vec4(bg, 1.0); return; }

  vec3 c = t.rgb;
  float u = vUv.x;
  float v = 1.0 - vUv.y;                      // 0 at the ground, 1 over the roof
  vec2 np = vec2(u * 6.0 + uSpin, v * 6.0);   // noise travels with the car as it turns
  float low = 1.0 - smoothstep(0.08, 0.7, v);
  float lum = dot(c, vec3(0.299, 0.587, 0.114));

  // Road grime: patchy, worst down low, and it dulls the paint rather than tinting it.
  float grime = fbm(np * 1.6) * 0.7 + 0.32;
  float dirt = clamp(uDirt * smoothstep(uWashX - 0.06, uWashX + 0.02, u) * grime * mix(0.45, 1.0, low), 0.0, 1.0);
  c = mix(c, vec3(lum * 0.66) + vec3(0.14, 0.12, 0.1), dirt * 0.82);

  // Bonded contamination: what you feel before you see it.
  float specks = step(0.981, hash21(floor(vec2(u * 430.0 + uSpin * 40.0, v * 430.0))))
               * uSpeck * smoothstep(uClayX - 0.05, uClayX + 0.02, u);
  c = mix(c, vec3(0.1, 0.095, 0.085), specks * 0.85);

  // Iron remover reacting: violet, in thin drips that run downhill.
  float drip = fbm(vec2(u * 95.0 + uSpin * 12.0, v * 1.5 - uTime * 0.11));
  float run = smoothstep(0.42, 0.72, drip);
  float blotch = smoothstep(0.3, 0.66, fbm(np * 1.15 + 3.7));
  float reach = smoothstep(uIronRun - 0.18, uIronRun + 0.1, v);
  float iron = clamp(uIron * run * blotch * mix(0.5, 1.0, low) * reach, 0.0, 1.0);
  c = mix(c, vec3(0.3, 0.012, 0.23) * (0.45 + lum * 1.1), iron * 0.94);

  // The coating: contrast comes up, then water pulls itself into beads.
  c = mix(c, clamp((c - 0.5) * 1.18 + 0.5, 0.0, 1.0), uGloss * 0.85);
  vec2 bp = vec2(u * 140.0 + uSpin * 26.0, v * 140.0);
  vec2 id = floor(bp);
  float r = hash21(id);
  float r2 = hash21(id + 7.3);
  vec2 f = fract(bp) - 0.5 - (vec2(r, r2) - 0.5) * 0.6;
  float d = length(f) * (0.62 + r * 0.95);
  float on = step(0.58, r2) * uBeads * smoothstep(0.05, 0.3, lum);
  c += smoothstep(0.38, 0.1, d) * on * (0.26 + 0.46 * lum) * vec3(0.9, 0.96, 1.0);
  c -= smoothstep(0.46, 0.38, d) * on * 0.13;

  // Snow foam pouring down over the lot.
  float foamLine = mix(1.16, -0.12, uFoam);
  float fn = fbm(np * 2.1 + vec2(0.0, -uTime * 0.22));
  float foam = clamp(smoothstep(foamLine - 0.17, foamLine + 0.06, v + (fn - 0.5) * 0.3) * uFoamFade, 0.0, 1.0);
  float bubbles = smoothstep(0.42, 0.74, fbm(np * 9.0)) * 0.09;
  vec3 foamCol = vec3(0.95, 0.965, 0.99) * (0.6 + 0.58 * lum) - bubbles;
  c = mix(c, foamCol, foam * 0.93);

  // The wet edge that follows the mitt along the panel.
  c = mix(c, vec3(0.88, 0.92, 0.96), exp(-pow((u - uWashX) / 0.05, 2.0)) * uDirt * 0.42);

  outColor = vec4(mix(bg, c, car), 1.0);
}`;

function compile(gl: WebGL2RenderingContext, type: number, src: string) {
  const s = gl.createShader(type)!;
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) ?? "shader");
  return s;
}

export function createCarSpin(canvas: HTMLCanvasElement, frames: string[], opts: Opts): CarSpin {
  const { reduced, onReady } = opts;
  const gl = canvas.getContext("webgl2", { alpha: false, antialias: false });
  if (!gl) throw new Error("no webgl2");

  const prog = gl.createProgram()!;
  gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VERT));
  gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog) ?? "link");
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, "aPos");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);

  const U = (n: string) => gl.getUniformLocation(prog, n);
  const u = {
    time: U("uTime"), dirt: U("uDirt"), washX: U("uWashX"), foam: U("uFoam"), foamFade: U("uFoamFade"),
    speck: U("uSpeck"), clayX: U("uClayX"), iron: U("uIron"), ironRun: U("uIronRun"),
    gloss: U("uGloss"), beads: U("uBeads"), spin: U("uSpin"),
  };

  // ------------------------------------------------------------------ frames
  const images: (HTMLImageElement | null)[] = new Array(frames.length).fill(null);
  let loaded = 0;
  let shown = -1;
  let ready = false;

  const load = (i: number) =>
    new Promise<void>((resolve) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = () => {
        images[i] = img;
        loaded++;
        if (!ready) {
          ready = true;
          onReady();
        }
        resolve();
      };
      img.onerror = () => resolve();
      img.src = frames[i];
    });

  // The first frame as fast as possible, then the rest fill in behind it.
  void load(0).then(async () => {
    for (let i = 1; i < frames.length; i++) await load(i);
  });

  const nearestLoaded = (i: number) => {
    for (let d = 0; d < frames.length; d++) {
      const a = images[(i + d) % frames.length];
      if (a) return (i + d) % frames.length;
      const b = images[(i - d + frames.length) % frames.length];
      if (b) return (i - d + frames.length) % frames.length;
    }
    return -1;
  };

  // ------------------------------------------------------------- interaction
  let angle = 0.12; // turns, 0..1 around the car
  let target = angle;
  let dragging = false;
  let lastX = 0;
  let idleSince = performance.now();

  const onDown = (e: PointerEvent) => {
    dragging = true;
    lastX = e.clientX;
    canvas.setPointerCapture(e.pointerId);
  };
  const onMove = (e: PointerEvent) => {
    if (!dragging) return;
    target -= (e.clientX - lastX) / Math.max(240, canvas.clientWidth * 0.85);
    lastX = e.clientX;
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

  const drive = (t: number) => {
    const at = (dur: number, delay = 0, ease = easeOut) => (reduced ? 1 : ease(clamp01((t - delay) / dur)));
    const set = (dirt = 0, washX = -0.3, foam = 0, foamFade = 1, speck = 0, clayX = -0.3, iron = 0, ironRun = 1.3, gloss = 0, beads = 0) => {
      gl.uniform1f(u.dirt, dirt); gl.uniform1f(u.washX, washX);
      gl.uniform1f(u.foam, foam); gl.uniform1f(u.foamFade, foamFade);
      gl.uniform1f(u.speck, speck); gl.uniform1f(u.clayX, clayX);
      gl.uniform1f(u.iron, iron); gl.uniform1f(u.ironRun, ironRun);
      gl.uniform1f(u.gloss, gloss); gl.uniform1f(u.beads, beads);
    };
    gl.uniform1f(u.time, reduced ? 0 : clock);

    if (step === "foam") set(1, -0.3, at(2.4));
    else if (step === "wash") set(1, mix(-0.3, 1.3, at(2.8, 0.7, easeInOut)), 1, 1 - at(1.1, 0, easeInOut));
    else {
      const sweep = at(3, 0.4, easeInOut);
      if (step === "clay") set(0, -0.3, 0, 1, 1, mix(-0.3, 1.3, sweep), 0, 1.3, sweep * 0.35);
      else if (step === "iron") set(0, -0.3, 0, 1, 0, -0.3, at(1.2), mix(1.3, -0.25, at(3.4, 0.3)));
      else set(0, -0.3, 0, 1, 0, -0.3, 0, 1.3, at(1.8), at(2.2, 1.1));
    }
  };

  // ------------------------------------------------------------------- loop
  let active = true;
  let raf = 0;
  let last = performance.now();
  let w = 0;
  let h = 0;

  const resize = () => {
    const r = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio, 2);
    const nw = Math.max(1, Math.round(r.width * dpr));
    const nh = Math.max(1, Math.round(r.height * dpr));
    if (nw === w && nh === h) return;
    w = nw; h = nh;
    canvas.width = w; canvas.height = h;
    gl.viewport(0, 0, w, h);
  };
  const ro = new ResizeObserver(resize);
  ro.observe(canvas);

  const frame = (now: number) => {
    raf = requestAnimationFrame(frame);
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (!active || !ready) return;
    clock += dt;
    resize();

    if (!reduced && !dragging && now - idleSince > 2200) target += dt * 0.022;
    angle += (target - angle) * (reduced ? 1 : 0.16);

    const idx = ((Math.round(angle * frames.length) % frames.length) + frames.length) % frames.length;
    const use = images[idx] ? idx : nearestLoaded(idx);
    if (use < 0) return;
    if (use !== shown) {
      shown = use;
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, images[use]!);
    }

    gl.uniform1f(u.spin, use * 0.37);
    drive(clock - stepStart);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
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
      gl.deleteTexture(tex);
      gl.deleteBuffer(buf);
      gl.deleteProgram(prog);
      images.fill(null);
      void loaded;
    },
  };
}
