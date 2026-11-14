// Scene shading: metallic-roughness GGX with one sun (shadow-mapped), one warm point
// light (the melt and heater glow), a sky/ground ambient term with a studio soft box,
// procedural surface textures chosen per vertex, a nameplate decal, and a cutaway plane.
// Post: depth prepass -> screen-space occlusion (raw, blur, apply), bright pass, blur for
// bloom, ACES tone map into display sRGB.

struct Globals {
    view_proj: mat4x4<f32>,
    light_vp: mat4x4<f32>,
    cam_pos: vec4<f32>,
    sun_dir: vec4<f32>,   // xyz: towards the sun
    sun_col: vec4<f32>,   // rgb: radiance
    pt_pos: vec4<f32>,    // xyz: position, w: falloff radius
    pt_col: vec4<f32>,    // rgb: intensity
    clip: vec4<f32>,      // xyz: plane normal, w: offset (points with dot > w are cut)
    sky: vec4<f32>,
    ground: vec4<f32>,
    misc: vec4<f32>,      // x: time (s), y: shadow texel size
};

@group(0) @binding(0) var<uniform> g: Globals;
@group(0) @binding(1) var shadow_map: texture_depth_2d;
@group(0) @binding(2) var shadow_samp: sampler_comparison;
@group(0) @binding(3) var decal_tex: texture_2d<f32>;
@group(0) @binding(4) var decal_samp: sampler;

struct VsIn {
    @location(0) pos: vec4<f32>,
    @location(1) nrm: vec4<f32>,
    @location(2) alb: vec4<f32>,
    @location(3) mat: vec4<f32>,
    @location(4) emi: vec4<f32>,
};

struct VsOut {
    @builtin(position) clip_pos: vec4<f32>,
    @location(0) wp: vec3<f32>,
    @location(1) n: vec3<f32>,
    @location(2) alb: vec4<f32>,
    @location(3) mat: vec4<f32>,
    @location(4) emi: vec3<f32>,
    @location(5) tex: f32,
};

@vertex
fn vs_main(v: VsIn) -> VsOut {
    var o: VsOut;
    o.clip_pos = g.view_proj * vec4<f32>(v.pos.xyz, 1.0);
    o.wp = v.pos.xyz;
    o.n = v.nrm.xyz;
    o.alb = v.alb;
    o.mat = v.mat;
    o.emi = v.emi.xyz;
    o.tex = v.emi.w;
    return o;
}

struct ShadowOut {
    @builtin(position) clip_pos: vec4<f32>,
    @location(0) wp: vec3<f32>,
    @location(1) cut: f32,
};

@vertex
fn vs_shadow(v: VsIn) -> ShadowOut {
    var o: ShadowOut;
    o.clip_pos = g.light_vp * vec4<f32>(v.pos.xyz, 1.0);
    o.wp = v.pos.xyz;
    o.cut = v.mat.w;
    return o;
}

@fragment
fn fs_shadow(i: ShadowOut) {
    if (i.cut > 0.5 && dot(i.wp, g.clip.xyz) > g.clip.w) {
        discard;
    }
}

@fragment
fn fs_depth(i: VsOut) {
    if (i.mat.w > 0.5 && dot(i.wp, g.clip.xyz) > g.clip.w) {
        discard;
    }
}

// ---- hashing and noise ----

fn hash3(p: vec3<f32>) -> f32 {
    let q = fract(p * 0.1031);
    let r = q + dot(q, q.zyx + 31.32);
    return fract((r.x + r.y) * r.z);
}

fn vnoise(p: vec3<f32>) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let u = f * f * (3.0 - 2.0 * f);
    let a = hash3(i);
    let b = hash3(i + vec3<f32>(1.0, 0.0, 0.0));
    let c = hash3(i + vec3<f32>(0.0, 1.0, 0.0));
    let d = hash3(i + vec3<f32>(1.0, 1.0, 0.0));
    let e = hash3(i + vec3<f32>(0.0, 0.0, 1.0));
    let f1 = hash3(i + vec3<f32>(1.0, 0.0, 1.0));
    let h = hash3(i + vec3<f32>(0.0, 1.0, 1.0));
    let k = hash3(i + vec3<f32>(1.0, 1.0, 1.0));
    let x0 = mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
    let x1 = mix(mix(e, f1, u.x), mix(h, k, u.x), u.y);
    return mix(x0, x1, u.z);
}

fn fbm(p: vec3<f32>) -> f32 {
    var s = 0.0;
    var a = 0.5;
    var q = p;
    for (var k = 0; k < 4; k++) {
        s += a * vnoise(q);
        q = q * 2.03 + vec3<f32>(1.7, 9.2, 3.1);
        a *= 0.5;
    }
    return s;
}

// ---- BRDF ----

fn d_ggx(ndh: f32, a2: f32) -> f32 {
    let d = ndh * ndh * (a2 - 1.0) + 1.0;
    return a2 / (3.14159265 * d * d + 1e-7);
}

fn g_smith(ndv: f32, ndl: f32, a: f32) -> f32 {
    let k = (a + 1.0) * (a + 1.0) / 8.0;
    let gv = ndv / (ndv * (1.0 - k) + k);
    let gl = ndl / (ndl * (1.0 - k) + k);
    return gv * gl;
}

// The BRDF times the cosine term for light direction l.
fn brdf(n: vec3<f32>, v: vec3<f32>, l: vec3<f32>, alb: vec3<f32>, metal: f32, rough: f32) -> vec3<f32> {
    let h = normalize(v + l);
    let ndl = max(dot(n, l), 0.0);
    let ndv = max(dot(n, v), 1e-3);
    let ndh = max(dot(n, h), 0.0);
    let vdh = max(dot(v, h), 0.0);
    let a = rough * rough;
    let f0 = mix(vec3<f32>(0.04), alb, metal);
    let f = f0 + (vec3<f32>(1.0) - f0) * pow(1.0 - vdh, 5.0);
    let spec = d_ggx(ndh, a * a) * g_smith(ndv, ndl, rough) * f / (4.0 * ndv * max(ndl, 1e-3) + 1e-4);
    let diff = (vec3<f32>(1.0) - f) * (1.0 - metal) * alb / 3.14159265;
    return (diff + spec) * ndl;
}

// Sun shadow with 3x3 percentage-closer filtering. Samples unconditionally so the
// texture reads stay in uniform control flow; out-of-map points are lit.
fn sun_shadow(wp: vec3<f32>, n: vec3<f32>) -> f32 {
    let lp = g.light_vp * vec4<f32>(wp + n * 4.0, 1.0);
    let p = lp.xyz / lp.w;
    let uv = vec2<f32>(p.x * 0.5 + 0.5, 1.0 - (p.y * 0.5 + 0.5));
    let depth = p.z - 0.0008;
    var s = 0.0;
    for (var y = -1; y <= 1; y++) {
        for (var x = -1; x <= 1; x++) {
            let o = vec2<f32>(f32(x), f32(y)) * g.misc.y;
            s += textureSampleCompare(shadow_map, shadow_samp, clamp(uv + o, vec2<f32>(0.0), vec2<f32>(1.0)), clamp(depth, 0.0, 1.0));
        }
    }
    let inside = uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0 && p.z <= 1.0;
    return select(1.0, s / 9.0, inside);
}

// ---- the nameplate on the chamber wall: a decal on the inner wall at angle 0 ----
const DECAL_A0: f32 = -0.8;
const DECAL_A1: f32 = 0.8;
const DECAL_Y0: f32 = -640.0;
const DECAL_Y1: f32 = -240.0;

// Returns (decal colour, 1) where the plate is, else (0, 0).
fn decal_at(wp: vec3<f32>) -> vec4<f32> {
    let a = atan2(wp.z, wp.x);
    if (a < DECAL_A0 || a > DECAL_A1 || wp.y < DECAL_Y0 || wp.y > DECAL_Y1) {
        return vec4<f32>(0.0);
    }
    let u = (a - DECAL_A0) / (DECAL_A1 - DECAL_A0);
    let v = (wp.y - DECAL_Y0) / (DECAL_Y1 - DECAL_Y0);
    let c = textureSampleLevel(decal_tex, decal_samp, vec2<f32>(u, 1.0 - v), 0.0);
    return vec4<f32>(c.rgb, 1.0);
}

// Procedural surface textures, by the vertex's texture id:
// 1 diamond tread plate, 2 graphite grain, 3 chamber steel with welds and the plate,
// 4 copper with patina. 0 leaves the material as it is.
// Returns albedo, (roughness, metallic, _) and normal.
struct Surf {
    alb: vec3<f32>,
    rough: f32,
    metal: f32,
    n: vec3<f32>,
};

fn textured(wp: vec3<f32>, t: f32, s_in: Surf) -> Surf {
    var s = s_in;
    if (t > 0.5 && t < 1.5) {
        // diamond tread: raised lozenges on a grid in the floor plane
        let u = (wp.x + wp.z) / 70.0;
        let v = (wp.x - wp.z) / 70.0;
        let bump = smoothstep(0.80, 0.98, abs(sin(3.14159265 * u) * sin(3.14159265 * v)));
        s.alb = s.alb * (0.78 + 0.22 * bump) * (0.9 + 0.2 * vnoise(wp * 0.08));
        s.rough = clamp(s.rough + 0.12 * (1.0 - bump) + 0.1 * vnoise(wp * 0.2), 0.0, 1.0);
        s.n = normalize(s.n + 0.08 * vec3<f32>(sin(3.14159265 * u), 0.0, sin(3.14159265 * v)));
    }
    if (t > 1.5 && t < 2.5) {
        // graphite: fine grain and a matte, slightly uneven surface
        let grain = vnoise(wp * 0.9) * 0.6 + vnoise(wp * 0.15) * 0.4;
        s.alb = s.alb * (0.7 + 0.6 * grain);
        s.rough = clamp(s.rough + 0.25 * (grain - 0.5), 0.2, 1.0);
    }
    if (t > 2.5 && t < 3.5) {
        // steel: horizontal weld seams every 400 mm, faint staining near the floor
        let seam = smoothstep(0.02, 0.0, abs(fract(wp.y / 400.0) - 0.5) - 0.48);
        s.alb = s.alb * (1.0 - 0.18 * seam) * (0.95 + 0.1 * vnoise(wp * 0.05));
        s.rough = clamp(s.rough + 0.2 * seam, 0.0, 1.0);
        let stain = smoothstep(-900.0, -1000.0, wp.y) * vnoise(wp * 0.02);
        s.alb = mix(s.alb, vec3<f32>(0.2, 0.17, 0.12), stain * 0.35);
        let d = decal_at(wp);
        if (d.a > 0.5) {
            s.alb = d.rgb;
            s.rough = 0.45;
            s.metal = 0.35;
        }
    }
    if (t > 3.5 && t < 4.5) {
        // copper: a green-brown patina in streaks
        let patina = fbm(wp * 0.06);
        s.alb = mix(s.alb, vec3<f32>(0.25, 0.35, 0.28), smoothstep(0.55, 0.75, patina) * 0.5);
        s.rough = clamp(s.rough + 0.15 * patina, 0.0, 1.0);
    }
    return s;
}

fn shade(i: VsOut, v: vec3<f32>, n_in: vec3<f32>) -> vec3<f32> {
    var n = n_in;
    var alb = i.alb.rgb;
    var metal = i.alb.a;
    var rough = clamp(i.mat.x, 0.04, 1.0);
    var emit = i.emi;
    let kind = i.mat.z;

    if (kind > 2.5 && kind < 3.5) {
        // felt: fibrous mottling and a rough, slightly lumpy surface
        let f = fbm(i.wp * 0.045);
        let fine = vnoise(i.wp * 0.6);
        alb = alb * (0.55 + 0.8 * f) * (0.85 + 0.3 * fine);
        rough = clamp(0.85 + 0.15 * fine, 0.0, 1.0);
        n = normalize(n + 0.18 * (vec3<f32>(vnoise(i.wp * 0.4), vnoise(i.wp * 0.4 + 7.3), vnoise(i.wp * 0.4 + 3.1)) - 0.5));
    }
    if (kind > 1.5 && kind < 2.5) {
        // melt: a churning surface, brighter in the convection cells
        let t = g.misc.x;
        let cell = fbm(vec3<f32>(i.wp.x * 0.012 + t * 0.05, 0.0, i.wp.z * 0.012 - t * 0.04));
        emit = emit * (0.6 + 0.9 * cell);
        alb = vec3<f32>(0.03, 0.02, 0.015);
        rough = 0.04;
        metal = 0.0;
    }
    if (kind > 3.5 && kind < 4.5) {
        // silicon: dark blue-grey with a faint lattice sheen
        let s = vnoise(i.wp * 0.05);
        alb = alb * (0.9 + 0.2 * s);
    }
    if (metal > 0.9 && kind < 0.5 && i.tex < 0.5) {
        // brushed metal: streaks along the surface, so reflections break up unevenly
        let streak = vnoise(vec3<f32>(i.wp.x * 0.03, i.wp.y * 0.9, i.wp.z * 0.03));
        rough = clamp(rough * (0.8 + 0.5 * streak), 0.04, 1.0);
        alb = alb * (0.92 + 0.12 * streak);
    }
    if (i.tex > 0.5) {
        let s = textured(i.wp, i.tex, Surf(alb, rough, metal, n));
        alb = s.alb;
        rough = s.rough;
        metal = s.metal;
        n = s.n;
    }

    let ndv = max(dot(n, v), 1e-3);
    let f0 = mix(vec3<f32>(0.04), alb, metal);

    // sun, shadowed
    let l_sun = normalize(g.sun_dir.xyz);
    let sh = sun_shadow(i.wp, n);
    var col = brdf(n, v, l_sun, alb, metal, rough) * g.sun_col.rgb * sh;

    // warm point light at the melt: falls off with distance
    let to_pt = g.pt_pos.xyz - i.wp;
    let d = length(to_pt);
    let l_pt = to_pt / max(d, 1e-3);
    let att = 1.0 / (1.0 + (d * d) / (g.pt_pos.w * g.pt_pos.w));
    col += brdf(n, v, l_pt, alb, metal, rough) * g.pt_col.rgb * att;

    // ambient: sky above, ground below; the specular term reflects the same environment
    let hemi = mix(g.ground.rgb, g.sky.rgb, n.y * 0.5 + 0.5);
    let r = reflect(-v, n);
    // studio environment: gradient plus a soft box where the sun is, for metal highlights
    let key = normalize(g.sun_dir.xyz);
    let box = pow(max(dot(r, key), 0.0), 10.0);
    let env = mix(g.ground.rgb, g.sky.rgb, clamp(r.y * 0.5 + 0.5, 0.0, 1.0)) + g.sun_col.rgb * box * 0.35;
    let fr = f0 + (max(vec3<f32>(1.0 - rough), f0) - f0) * pow(1.0 - ndv, 5.0);
    col += hemi * alb * (1.0 - metal) * 0.3;
    col += env * fr * (1.0 - rough * 0.6);
    return col + emit;
}

@fragment
fn fs_opaque(i: VsOut) -> @location(0) vec4<f32> {
    if (i.mat.w > 0.5 && dot(i.wp, g.clip.xyz) > g.clip.w) {
        discard;
    }
    let v = normalize(g.cam_pos.xyz - i.wp);
    var n = normalize(i.n);
    // two-sided: light the side the camera sees
    if (dot(n, v) < 0.0) {
        n = -n;
    }
    return vec4<f32>(shade(i, v, n), 1.0);
}

@fragment
fn fs_glass(i: VsOut) -> @location(0) vec4<f32> {
    if (i.mat.w > 0.5 && dot(i.wp, g.clip.xyz) > g.clip.w) {
        discard;
    }
    let v = normalize(g.cam_pos.xyz - i.wp);
    var n = normalize(i.n);
    if (dot(n, v) < 0.0) {
        n = -n;
    }
    if (i.mat.z > 5.5) {
        // clear glass: it transmits nearly all light, so the base and rim behind it keep their
        // own colour. Only a faint Fresnel reflection (sun glint, sky sheen) is added. Premultiplied,
        // like the rest of the glass.
        let fres_c = 0.04 + 0.96 * pow(1.0 - max(dot(n, v), 0.0), 5.0);
        var j = i;
        j.alb = vec4<f32>(0.0, 0.0, 0.0, 0.0);
        let refl = shade(j, v, n);
        let ac = clamp(i.mat.y + fres_c * 0.2, 0.0, 1.0);
        return vec4<f32>(refl * ac, ac);
    }
    let ndv = max(dot(n, v), 0.0);
    let fres = 0.04 + 0.96 * pow(1.0 - ndv, 5.0);
    let c = shade(i, v, n);
    let a = clamp(i.mat.y + fres * 0.8, 0.0, 1.0);
    // premultiplied, for the One / OneMinusSrcAlpha blend
    return vec4<f32>(c * a, a);
}

// ---- post ----

struct FsIn {
    @builtin(position) pos: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@vertex
fn vs_full(@builtin(vertex_index) vi: u32) -> FsIn {
    // one oversized triangle covering the screen
    let x = f32((vi << 1u) & 2u);
    let y = f32(vi & 2u);
    var o: FsIn;
    o.pos = vec4<f32>(x * 2.0 - 1.0, 1.0 - y * 2.0, 0.0, 1.0);
    o.uv = vec2<f32>(x, y);
    return o;
}

struct PostParams {
    a: vec4<f32>, // blur: dir.xy, texel.xy   | composite: bg rgb (display), _   | bright: threshold, _, _, _
    b: vec4<f32>, // composite: bloom strength, exposure, _, _
};

@group(0) @binding(0) var<uniform> pp: PostParams;
@group(0) @binding(1) var src_a: texture_2d<f32>;
@group(0) @binding(2) var src_b: texture_2d<f32>;
@group(0) @binding(3) var lin: sampler;

@fragment
fn fs_bright(i: FsIn) -> @location(0) vec4<f32> {
    let c = textureSample(src_a, lin, i.uv).rgb;
    let lum = max(max(c.r, c.g), c.b);
    let k = max(lum - pp.a.x, 0.0) / max(lum, 1e-4);
    return vec4<f32>(c * k, 1.0);
}

@fragment
fn fs_blur(i: FsIn) -> @location(0) vec4<f32> {
    let step = pp.a.xy * pp.a.zw;
    let w = array<f32, 5>(0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
    var c = textureSample(src_a, lin, i.uv).rgb * w[0];
    for (var k = 1; k < 5; k++) {
        let o = step * f32(k) * 2.0;
        c += textureSample(src_a, lin, i.uv + o).rgb * w[k];
        c += textureSample(src_a, lin, i.uv - o).rgb * w[k];
    }
    return vec4<f32>(c, 1.0);
}

fn aces(x: vec3<f32>) -> vec3<f32> {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), vec3<f32>(0.0), vec3<f32>(1.0));
}

// src_a is the HDR scene (premultiplied alpha), src_b the bloom
@fragment
fn fs_composite(i: FsIn) -> @location(0) vec4<f32> {
    let hdr = textureSample(src_a, lin, i.uv);
    let bloom = textureSample(src_b, lin, i.uv).rgb;
    // The scene is premultiplied by its coverage a. Un-premultiply before tone mapping, then lay
    // the foreground over the background by a. Tone-mapping the premultiplied value instead lifted
    // faint glass toward white over light backgrounds.
    let a = hdr.a;
    let c = hdr.rgb / max(a, 1e-4);
    let glow = bloom * pp.b.x * pp.b.y;
    let fg = pow(aces(c * pp.b.y + glow), vec3<f32>(1.0 / 2.2));
    let bgl = pp.a.rgb + pow(aces(glow), vec3<f32>(1.0 / 2.2));
    return vec4<f32>(a * fg + (1.0 - a) * bgl, 1.0);
}

// ---- screen-space ambient occlusion ----
// p: projection diagonal (x, y), near, far. s: near radius, bias, far radius, strength.
// d: size (w, h).
struct AoP {
    p: vec4<f32>,
    s: vec4<f32>,
    d: vec4<f32>,
};

@group(0) @binding(0) var<uniform> ao: AoP;
@group(0) @binding(1) var depth_tex: texture_depth_2d;
@group(0) @binding(2) var ao_a: texture_2d<f32>;
@group(0) @binding(3) var ao_b: texture_2d<f32>;

fn view_at(px: vec2<i32>) -> vec3<f32> {
    let dims = ao.d.xy;
    let c = clamp(px, vec2<i32>(0), vec2<i32>(dims) - vec2<i32>(1));
    let d = textureLoad(depth_tex, c, 0);
    let near = ao.p.z;
    let far = ao.p.w;
    let z = -(near * far) / (far + d * (near - far));
    let nx = (f32(c.x) + 0.5) / dims.x * 2.0 - 1.0;
    let ny = 1.0 - (f32(c.y) + 0.5) / dims.y * 2.0;
    return vec3<f32>(nx * (-z) / ao.p.x, ny * (-z) / ao.p.y, z);
}

fn to_px(v: vec3<f32>) -> vec2<i32> {
    let nx = ao.p.x * v.x / (-v.z);
    let ny = ao.p.y * v.y / (-v.z);
    let dims = ao.d.xy;
    return vec2<i32>(i32((nx * 0.5 + 0.5) * dims.x), i32((0.5 - ny * 0.5) * dims.y));
}

// Raw occlusion: 16 samples in a sphere around each point, 8 near and 8 far, each
// pixel rotated differently so the noise is fine and the blur can hide it.
@fragment
fn fs_ao_raw(i: FsIn) -> @location(0) vec4<f32> {
    let px = vec2<i32>(i.pos.xy);
    let dims = ao.d.xy;
    let c = clamp(px, vec2<i32>(0), vec2<i32>(dims) - vec2<i32>(1));
    if (textureLoad(depth_tex, c, 0) >= 0.99999) {
        return vec4<f32>(1.0);
    }
    let p = view_at(px);
    let dx = view_at(px + vec2<i32>(1, 0)) - p;
    let dy = view_at(px + vec2<i32>(0, 1)) - p;
    var n = normalize(cross(dx, dy));
    if (dot(n, -p) < 0.0) {
        n = -n;
    }
    let rot = f32(((px.x * 1973) + (px.y * 9277)) & 1023) * 0.0061359;
    let bias = ao.s.y;
    var occ = 0.0;
    let count = 16;
    for (var k = 0; k < count; k++) {
        let fk = f32(k);
        let zz = 1.0 - (fk + 0.5) / f32(count);
        let r2 = sqrt(max(0.0, 1.0 - zz * zz));
        let phi = fk * 2.39996323 + rot;
        var dir = vec3<f32>(r2 * cos(phi), r2 * sin(phi), zz);
        if (dot(dir, n) < 0.0) {
            dir = -dir;
        }
        let radius = select(ao.s.x, ao.s.z, k >= count / 2);
        let scale = 0.3 + 0.7 * fract(fk * 0.618 + rot * 0.1);
        let sp = p + dir * radius * scale;
        let sc = view_at(to_px(sp));
        let range = smoothstep(0.0, 1.0, radius / max(abs(p.z - sc.z), 1e-3));
        // the visible surface at the sample is in front of the sample point
        occ += select(0.0, range, sc.z > sp.z + bias);
    }
    let a = 1.0 - clamp(occ / f32(count) * ao.s.w, 0.0, 1.0);
    return vec4<f32>(a, a, a, 1.0);
}

// Blur of the raw occlusion over 7 taps along `dir`, weighted by depth so edges stay sharp.
// Run twice (across, then down): 14 taps a pixel instead of a 7x7 box's 49.
fn ao_blur_1d(px: vec2<i32>, dir: vec2<i32>) -> f32 {
    let z0 = view_at(px).z;
    let hi = vec2<i32>(ao.d.xy) - vec2<i32>(1);
    var sum = 0.0;
    var wsum = 0.0;
    for (var k = -3; k <= 3; k++) {
        let q = px + dir * k;
        let zq = view_at(q).z;
        let w = exp(-abs(zq - z0) / (0.03 * abs(z0) + 1.0));
        sum += textureLoad(ao_a, clamp(q, vec2<i32>(0), hi), 0).r * w;
        wsum += w;
    }
    return sum / max(wsum, 1e-4);
}

@fragment
fn fs_ao_blur_h(i: FsIn) -> @location(0) vec4<f32> {
    let a = ao_blur_1d(vec2<i32>(i.pos.xy), vec2<i32>(1, 0));
    return vec4<f32>(a, a, a, 1.0);
}

@fragment
fn fs_ao_blur_v(i: FsIn) -> @location(0) vec4<f32> {
    let a = ao_blur_1d(vec2<i32>(i.pos.xy), vec2<i32>(0, 1));
    return vec4<f32>(a, a, a, 1.0);
}

// Multiplies the scene (ao_b) by the blurred occlusion (ao_a).
@fragment
fn fs_ao_apply(i: FsIn) -> @location(0) vec4<f32> {
    let px = vec2<i32>(i.pos.xy);
    let scene = textureLoad(ao_b, px, 0);
    let a = textureLoad(ao_a, px, 0).r;
    return vec4<f32>(scene.rgb * a, scene.a);
}
