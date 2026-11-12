//! The headless GPU renderer: shadow map, 4x MSAA HDR scene, glass, bloom, tone map,
//! and a read-back to RGBA8. One instance is kept per process (see `with_renderer`).

use bytemuck::{Pod, Zeroable};
use image::RgbaImage;
use std::sync::{Mutex, OnceLock};
use wgpu::util::DeviceExt;

use crate::math::{M4, V3};
use crate::mesh::Mesh;

const SHADOW_SIZE: u32 = 2048;
const MSAA: u32 = 4;
const HDR: wgpu::TextureFormat = wgpu::TextureFormat::Rgba16Float;
const DEPTH: wgpu::TextureFormat = wgpu::TextureFormat::Depth32Float;

/// Everything the shaders read per frame. Layout must match `struct Globals`.
#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
pub struct Globals {
    pub view_proj: [[f32; 4]; 4],
    pub light_vp: [[f32; 4]; 4],
    pub cam_pos: [f32; 4],
    pub sun_dir: [f32; 4],
    pub sun_col: [f32; 4],
    pub pt_pos: [f32; 4],
    pub pt_col: [f32; 4],
    pub clip: [f32; 4],
    pub sky: [f32; 4],
    pub ground: [f32; 4],
    pub misc: [f32; 4],
}

#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
struct PostParams {
    a: [f32; 4],
    b: [f32; 4],
}

/// Lighting and camera for one frame, in world units (mm, Y up).
#[derive(Clone, Copy, Debug)]
pub struct Frame {
    pub view_proj: M4,
    pub light_vp: M4,
    pub cam_pos: V3,
    pub sun_dir: V3,
    pub sun_col: V3,
    pub pt_pos: V3,
    pub pt_radius: f32,
    pub pt_col: V3,
    /// Cutaway plane: points with dot(p, normal) > offset are removed on cut surfaces.
    pub clip_n: V3,
    pub clip_d: f32,
    pub sky: V3,
    pub ground: V3,
    pub time: f32,
    /// Display-space background colour, matched to the terminal.
    pub bg: [f32; 3],
    pub bloom: f32,
    pub exposure: f32,
    /// projection diagonal (x, y), near and far: for reconstructing view space from depth
    pub proj_diag: [f32; 2],
    pub near_far: [f32; 2],
    /// ambient occlusion radius (world units) and strength
    pub ao_radius: f32,
    pub ao_strength: f32,
}

struct Targets {
    w: u32,
    h: u32,
    msaa_color: wgpu::TextureView,
    hdr_view: wgpu::TextureView,
    hdr2_view: wgpu::TextureView,
    depth1_view: wgpu::TextureView,
    ao_raw_view: wgpu::TextureView,
    ao_blur_view: wgpu::TextureView,
    depth: wgpu::TextureView,
    bloom_a: wgpu::TextureView,
    bloom_b: wgpu::TextureView,
    out: wgpu::Texture,
    out_view: wgpu::TextureView,
    read: wgpu::Buffer,
    padded_row: u32,
}

pub struct Renderer {
    device: wgpu::Device,
    queue: wgpu::Queue,
    globals_buf: wgpu::Buffer,
    bg_shadow: wgpu::BindGroup,
    bg_main: wgpu::BindGroup,
    shadow_view: wgpu::TextureView,
    shadow_pipe: wgpu::RenderPipeline,
    opaque_pipe: wgpu::RenderPipeline,
    glass_pipe: wgpu::RenderPipeline,
    depth_pipe: wgpu::RenderPipeline,
    ao_raw_pipe: wgpu::RenderPipeline,
    ao_blur_pipe: wgpu::RenderPipeline,
    ao_apply_pipe: wgpu::RenderPipeline,
    bgl_ao: wgpu::BindGroupLayout,
    ao_buf: wgpu::Buffer,
    bright_pipe: wgpu::RenderPipeline,
    blur_pipe: wgpu::RenderPipeline,
    comp_pipe: wgpu::RenderPipeline,
    post_bgl: wgpu::BindGroupLayout,
    comp_bgl: wgpu::BindGroupLayout,
    lin: wgpu::Sampler,
    params_buf: [wgpu::Buffer; 4],
    targets: Option<Targets>,
}

static RENDERER: OnceLock<Mutex<Renderer>> = OnceLock::new();

/// Runs `f` on the process's renderer, creating the GPU device on first use.
pub fn with_renderer<T>(f: impl FnOnce(&mut Renderer) -> T) -> T {
    let m = RENDERER.get_or_init(|| Mutex::new(Renderer::new()));
    let mut r = m.lock().unwrap_or_else(|e| e.into_inner());
    f(&mut r)
}

fn pad256(n: u32) -> u32 {
    n.div_ceil(256) * 256
}

impl Renderer {
    pub fn new() -> Renderer {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor::new_without_display_handle());
        let adapter = pollster::block_on(instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            compatible_surface: None,
            force_fallback_adapter: false,
            apply_limit_buckets: false,
        }))
        .expect("no GPU adapter for the realistic renderer");
        let (device, queue) = pollster::block_on(adapter.request_device(&wgpu::DeviceDescriptor {
            label: Some("pbr3d"),
            required_features: wgpu::Features::empty(),
            required_limits: wgpu::Limits::default(),
            experimental_features: wgpu::ExperimentalFeatures::disabled(),
            memory_hints: wgpu::MemoryHints::Performance,
            trace: wgpu::Trace::Off,
        }))
        .expect("no GPU device");

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("scene"),
            source: wgpu::ShaderSource::Wgsl(include_str!("shaders.wgsl").into()),
        });

        let globals_buf = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("globals"),
            size: std::mem::size_of::<Globals>() as u64,
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        let shadow_tex = device.create_texture(&wgpu::TextureDescriptor {
            label: Some("shadow"),
            size: wgpu::Extent3d { width: SHADOW_SIZE, height: SHADOW_SIZE, depth_or_array_layers: 1 },
            mip_level_count: 1,
            sample_count: 1,
            dimension: wgpu::TextureDimension::D2,
            format: DEPTH,
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::TEXTURE_BINDING,
            view_formats: &[],
        });
        let shadow_view = shadow_tex.create_view(&wgpu::TextureViewDescriptor::default());
        let shadow_samp = device.create_sampler(&wgpu::SamplerDescriptor {
            label: Some("shadow samp"),
            address_mode_u: wgpu::AddressMode::ClampToEdge,
            address_mode_v: wgpu::AddressMode::ClampToEdge,
            address_mode_w: wgpu::AddressMode::ClampToEdge,
            mag_filter: wgpu::FilterMode::Linear,
            min_filter: wgpu::FilterMode::Linear,
            compare: Some(wgpu::CompareFunction::LessEqual),
            ..Default::default()
        });
        let lin = device.create_sampler(&wgpu::SamplerDescriptor {
            label: Some("lin"),
            address_mode_u: wgpu::AddressMode::ClampToEdge,
            address_mode_v: wgpu::AddressMode::ClampToEdge,
            address_mode_w: wgpu::AddressMode::ClampToEdge,
            mag_filter: wgpu::FilterMode::Linear,
            min_filter: wgpu::FilterMode::Linear,
            ..Default::default()
        });

        let vis = wgpu::ShaderStages::VERTEX_FRAGMENT;
        let bgl_shadow = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("bgl shadow"),
            entries: &[wgpu::BindGroupLayoutEntry {
                binding: 0,
                visibility: vis,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Uniform,
                    has_dynamic_offset: false,
                    min_binding_size: None,
                },
                count: None,
            }],
        });
        let bgl_main = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("bgl main"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: vis,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Uniform,
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: vis,
                    ty: wgpu::BindingType::Texture {
                        sample_type: wgpu::TextureSampleType::Depth,
                        view_dimension: wgpu::TextureViewDimension::D2,
                        multisampled: false,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 2,
                    visibility: vis,
                    ty: wgpu::BindingType::Sampler(wgpu::SamplerBindingType::Comparison),
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 3,
                    visibility: vis,
                    ty: wgpu::BindingType::Texture {
                        sample_type: wgpu::TextureSampleType::Float { filterable: true },
                        view_dimension: wgpu::TextureViewDimension::D2,
                        multisampled: false,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 4,
                    visibility: vis,
                    ty: wgpu::BindingType::Sampler(wgpu::SamplerBindingType::Filtering),
                    count: None,
                },
            ],
        });
        let bg_shadow = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("bg shadow"),
            layout: &bgl_shadow,
            entries: &[wgpu::BindGroupEntry { binding: 0, resource: globals_buf.as_entire_binding() }],
        });
        // the nameplate: a 5x7 font baked into an RGBA atlas
        let (aw, ah, apx) = crate::font::atlas(&["CZOCHRALSKI", "PULLER 300MM"], 4);
        let decal = device.create_texture(&wgpu::TextureDescriptor {
            label: Some("nameplate"),
            size: wgpu::Extent3d { width: aw, height: ah, depth_or_array_layers: 1 },
            mip_level_count: 1,
            sample_count: 1,
            dimension: wgpu::TextureDimension::D2,
            format: wgpu::TextureFormat::Rgba8Unorm,
            usage: wgpu::TextureUsages::TEXTURE_BINDING | wgpu::TextureUsages::COPY_DST,
            view_formats: &[],
        });
        queue.write_texture(
            wgpu::TexelCopyTextureInfo { texture: &decal, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
            &apx,
            wgpu::TexelCopyBufferLayout { offset: 0, bytes_per_row: Some(aw * 4), rows_per_image: Some(ah) },
            wgpu::Extent3d { width: aw, height: ah, depth_or_array_layers: 1 },
        );
        let decal_view = decal.create_view(&wgpu::TextureViewDescriptor::default());
        let decal_samp = device.create_sampler(&wgpu::SamplerDescriptor {
            label: Some("decal samp"),
            address_mode_u: wgpu::AddressMode::ClampToEdge,
            address_mode_v: wgpu::AddressMode::ClampToEdge,
            address_mode_w: wgpu::AddressMode::ClampToEdge,
            mag_filter: wgpu::FilterMode::Linear,
            min_filter: wgpu::FilterMode::Linear,
            ..Default::default()
        });
        let bg_main = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("bg main"),
            layout: &bgl_main,
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: globals_buf.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 1, resource: wgpu::BindingResource::TextureView(&shadow_view) },
                wgpu::BindGroupEntry { binding: 2, resource: wgpu::BindingResource::Sampler(&shadow_samp) },
                wgpu::BindGroupEntry { binding: 3, resource: wgpu::BindingResource::TextureView(&decal_view) },
                wgpu::BindGroupEntry { binding: 4, resource: wgpu::BindingResource::Sampler(&decal_samp) },
            ],
        });

        let vertex_layout = wgpu::VertexBufferLayout {
            array_stride: std::mem::size_of::<crate::mesh::Vertex>() as u64,
            step_mode: wgpu::VertexStepMode::Vertex,
            attributes: &wgpu::vertex_attr_array![
                0 => Float32x4, 1 => Float32x4, 2 => Float32x4, 3 => Float32x4, 4 => Float32x4
            ],
        };
        let pl_shadow = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pl shadow"),
            bind_group_layouts: &[Some(&bgl_shadow)],
            immediate_size: 0,
        });
        let pl_main = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pl main"),
            bind_group_layouts: &[Some(&bgl_main)],
            immediate_size: 0,
        });
        let shadow_pipe = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("shadow"),
            layout: Some(&pl_shadow),
            vertex: wgpu::VertexState {
                module: &shader,
                entry_point: Some("vs_shadow"),
                compilation_options: Default::default(),
                buffers: &[Some(vertex_layout.clone())],
            },
            primitive: wgpu::PrimitiveState { cull_mode: None, ..Default::default() },
            depth_stencil: Some(wgpu::DepthStencilState {
                format: DEPTH,
                depth_write_enabled: Some(true),
                depth_compare: Some(wgpu::CompareFunction::Less),
                stencil: Default::default(),
                bias: wgpu::DepthBiasState { constant: 2, slope_scale: 2.0, clamp: 0.0 },
            }),
            multisample: wgpu::MultisampleState::default(),
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fs_shadow"),
                compilation_options: Default::default(),
                targets: &[],
            }),
            multiview_mask: None,
            cache: None,
        });
        let scene_pipe = |entry: &str, glass: bool| {
            device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
                label: Some(entry),
                layout: Some(&pl_main),
                vertex: wgpu::VertexState {
                    module: &shader,
                    entry_point: Some("vs_main"),
                    compilation_options: Default::default(),
                    buffers: &[Some(vertex_layout.clone())],
                },
                primitive: wgpu::PrimitiveState { cull_mode: None, ..Default::default() },
                depth_stencil: Some(wgpu::DepthStencilState {
                    format: DEPTH,
                    depth_write_enabled: Some(!glass),
                    depth_compare: Some(wgpu::CompareFunction::Less),
                    stencil: Default::default(),
                    bias: Default::default(),
                }),
                multisample: wgpu::MultisampleState { count: MSAA, mask: !0, alpha_to_coverage_enabled: false },
                fragment: Some(wgpu::FragmentState {
                    module: &shader,
                    entry_point: Some(entry),
                    compilation_options: Default::default(),
                    targets: &[Some(wgpu::ColorTargetState {
                        format: HDR,
                        blend: if glass {
                            Some(wgpu::BlendState {
                                color: wgpu::BlendComponent {
                                    src_factor: wgpu::BlendFactor::One,
                                    dst_factor: wgpu::BlendFactor::OneMinusSrcAlpha,
                                    operation: wgpu::BlendOperation::Add,
                                },
                                alpha: wgpu::BlendComponent {
                                    src_factor: wgpu::BlendFactor::One,
                                    dst_factor: wgpu::BlendFactor::OneMinusSrcAlpha,
                                    operation: wgpu::BlendOperation::Add,
                                },
                            })
                        } else {
                            None
                        },
                        write_mask: wgpu::ColorWrites::ALL,
                    })],
                }),
                multiview_mask: None,
                cache: None,
            })
        };
        let opaque_pipe = scene_pipe("fs_opaque", false);
        let glass_pipe = scene_pipe("fs_glass", true);

        // depth prepass (opaque, cut) feeding the occlusion pass
        let depth_pipe = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("depth"),
            layout: Some(&pl_shadow),
            vertex: wgpu::VertexState {
                module: &shader,
                entry_point: Some("vs_main"),
                compilation_options: Default::default(),
                buffers: &[Some(vertex_layout.clone())],
            },
            primitive: wgpu::PrimitiveState { cull_mode: None, ..Default::default() },
            depth_stencil: Some(wgpu::DepthStencilState {
                format: DEPTH,
                depth_write_enabled: Some(true),
                depth_compare: Some(wgpu::CompareFunction::Less),
                stencil: Default::default(),
                bias: Default::default(),
            }),
            multisample: wgpu::MultisampleState::default(),
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fs_depth"),
                compilation_options: Default::default(),
                targets: &[],
            }),
            multiview_mask: None,
            cache: None,
        });
        let bgl_ao = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("bgl ao"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Uniform, has_dynamic_offset: false, min_binding_size: None },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture { sample_type: wgpu::TextureSampleType::Depth, view_dimension: wgpu::TextureViewDimension::D2, multisampled: false },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 2,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture { sample_type: wgpu::TextureSampleType::Float { filterable: true }, view_dimension: wgpu::TextureViewDimension::D2, multisampled: false },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 3,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture { sample_type: wgpu::TextureSampleType::Float { filterable: true }, view_dimension: wgpu::TextureViewDimension::D2, multisampled: false },
                    count: None,
                },
            ],
        });
        let pl_ao = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pl ao"),
            bind_group_layouts: &[Some(&bgl_ao)],
            immediate_size: 0,
        });
        let ao_pipe_for = |entry: &str| {
            device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
                label: Some(entry),
                layout: Some(&pl_ao),
                vertex: wgpu::VertexState { module: &shader, entry_point: Some("vs_full"), compilation_options: Default::default(), buffers: &[] },
                primitive: Default::default(),
                depth_stencil: None,
                multisample: wgpu::MultisampleState::default(),
                fragment: Some(wgpu::FragmentState {
                    module: &shader,
                    entry_point: Some(entry),
                    compilation_options: Default::default(),
                    targets: &[Some(wgpu::ColorTargetState { format: HDR, blend: None, write_mask: wgpu::ColorWrites::ALL })],
                }),
                multiview_mask: None,
                cache: None,
            })
        };
        let ao_raw_pipe = ao_pipe_for("fs_ao_raw");
        let ao_blur_pipe = ao_pipe_for("fs_ao_blur");
        let ao_apply_pipe = ao_pipe_for("fs_ao_apply");
        let ao_buf = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("ao params"),
            size: 48,
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        // post-processing
        let post_bgl = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("bgl post"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Uniform,
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture {
                        sample_type: wgpu::TextureSampleType::Float { filterable: true },
                        view_dimension: wgpu::TextureViewDimension::D2,
                        multisampled: false,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 2,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture {
                        sample_type: wgpu::TextureSampleType::Float { filterable: true },
                        view_dimension: wgpu::TextureViewDimension::D2,
                        multisampled: false,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 3,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Sampler(wgpu::SamplerBindingType::Filtering),
                    count: None,
                },
            ],
        });
        // the composite uses the same layout; its second texture is the bloom
        let comp_bgl = post_bgl.clone();
        let pl_post = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pl post"),
            bind_group_layouts: &[Some(&post_bgl)],
            immediate_size: 0,
        });
        let post_pipe = |entry: &str, format: wgpu::TextureFormat| {
            device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
                label: Some(entry),
                layout: Some(&pl_post),
                vertex: wgpu::VertexState {
                    module: &shader,
                    entry_point: Some("vs_full"),
                    compilation_options: Default::default(),
                    buffers: &[],
                },
                primitive: Default::default(),
                depth_stencil: None,
                multisample: wgpu::MultisampleState::default(),
                fragment: Some(wgpu::FragmentState {
                    module: &shader,
                    entry_point: Some(entry),
                    compilation_options: Default::default(),
                    targets: &[Some(wgpu::ColorTargetState {
                        format,
                        blend: None,
                        write_mask: wgpu::ColorWrites::ALL,
                    })],
                }),
                multiview_mask: None,
                cache: None,
            })
        };
        let bright_pipe = post_pipe("fs_bright", HDR);
        let blur_pipe = post_pipe("fs_blur", HDR);
        let comp_pipe = post_pipe("fs_composite", wgpu::TextureFormat::Rgba8Unorm);

        let mk_params = |label: &str| {
            device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
                label: Some(label),
                contents: bytemuck::bytes_of(&PostParams { a: [0.0; 4], b: [0.0; 4] }),
                usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            })
        };
        let params_buf = [mk_params("p0"), mk_params("p1"), mk_params("p2"), mk_params("p3")];

        Renderer {
            device,
            queue,
            globals_buf,
            bg_shadow,
            bg_main,
            shadow_view,
            shadow_pipe,
            opaque_pipe,
            glass_pipe,
            depth_pipe,
            ao_raw_pipe,
            ao_blur_pipe,
            ao_apply_pipe,
            bgl_ao,
            ao_buf,
            bright_pipe,
            blur_pipe,
            comp_pipe,
            post_bgl,
            comp_bgl,
            lin,
            params_buf,
            targets: None,
        }
    }

    fn ensure_targets(&mut self, w: u32, h: u32) {
        if let Some(t) = &self.targets {
            if t.w == w && t.h == h {
                return;
            }
        }
        let d = &self.device;
        let tex = |label: &str, width: u32, height: u32, format: wgpu::TextureFormat, samples: u32, usage: wgpu::TextureUsages| {
            d.create_texture(&wgpu::TextureDescriptor {
                label: Some(label),
                size: wgpu::Extent3d { width: width.max(1), height: height.max(1), depth_or_array_layers: 1 },
                mip_level_count: 1,
                sample_count: samples,
                dimension: wgpu::TextureDimension::D2,
                format,
                usage,
                view_formats: &[],
            })
        };
        let rt = wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::TEXTURE_BINDING;
        let msaa = tex("msaa", w, h, HDR, MSAA, wgpu::TextureUsages::RENDER_ATTACHMENT);
        let hdr = tex("hdr", w, h, HDR, 1, rt);
        let hdr2 = tex("hdr2", w, h, HDR, 1, rt);
        let depth1 = tex("depth1", w, h, DEPTH, 1, rt);
        let ao_raw = tex("ao raw", w, h, HDR, 1, rt);
        let ao_blur = tex("ao blur", w, h, HDR, 1, rt);
        let depth = tex("depth", w, h, DEPTH, MSAA, wgpu::TextureUsages::RENDER_ATTACHMENT);
        let (hw, hh) = ((w / 2).max(1), (h / 2).max(1));
        let bloom_a = tex("bloom a", hw, hh, HDR, 1, rt);
        let bloom_b = tex("bloom b", hw, hh, HDR, 1, rt);
        let out = tex("out", w, h, wgpu::TextureFormat::Rgba8Unorm, 1, wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC);
        let padded_row = pad256(w * 4);
        let read = d.create_buffer(&wgpu::BufferDescriptor {
            label: Some("read"),
            size: (padded_row * h) as u64,
            usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
            mapped_at_creation: false,
        });
        let v = |t: &wgpu::Texture| t.create_view(&wgpu::TextureViewDescriptor::default());
        self.targets = Some(Targets {
            w,
            h,
            msaa_color: v(&msaa),
            hdr_view: v(&hdr),
            hdr2_view: v(&hdr2),
            depth1_view: v(&depth1),
            ao_raw_view: v(&ao_raw),
            ao_blur_view: v(&ao_blur),
            depth: v(&depth),
            bloom_a: v(&bloom_a),
            bloom_b: v(&bloom_b),
            out_view: v(&out),
            out,
            read,
            padded_row,
        });
    }

    /// Renders `solid` (opaque) and `glass` (alpha) meshes under `f` and returns the frame.
    pub fn render(&mut self, f: &Frame, solid: &Mesh, glass: &Mesh, w: u32, h: u32) -> RgbaImage {
        self.ensure_targets(w, h);
        let globals = Globals {
            view_proj: f.view_proj,
            light_vp: f.light_vp,
            cam_pos: [f.cam_pos[0], f.cam_pos[1], f.cam_pos[2], 1.0],
            sun_dir: [f.sun_dir[0], f.sun_dir[1], f.sun_dir[2], 0.0],
            sun_col: [f.sun_col[0], f.sun_col[1], f.sun_col[2], 1.0],
            pt_pos: [f.pt_pos[0], f.pt_pos[1], f.pt_pos[2], f.pt_radius],
            pt_col: [f.pt_col[0], f.pt_col[1], f.pt_col[2], 1.0],
            clip: [f.clip_n[0], f.clip_n[1], f.clip_n[2], f.clip_d],
            sky: [f.sky[0], f.sky[1], f.sky[2], 0.0],
            ground: [f.ground[0], f.ground[1], f.ground[2], 0.0],
            misc: [f.time, 1.0 / SHADOW_SIZE as f32, 0.0, 0.0],
        };
        self.queue.write_buffer(&self.globals_buf, 0, bytemuck::bytes_of(&globals));
        let params = [
            PostParams { a: [1.0, 0.0, 0.0, 0.0], b: [0.0; 4] },
            PostParams { a: [1.0, 0.0, 1.0 / (w / 2).max(1) as f32, 0.0], b: [0.0; 4] },
            PostParams { a: [0.0, 1.0, 0.0, 1.0 / (h / 2).max(1) as f32], b: [0.0; 4] },
            PostParams {
                a: [f.bg[0], f.bg[1], f.bg[2], 0.0],
                b: [f.bloom, f.exposure, 0.0, 0.0],
            },
        ];
        for (i, p) in params.iter().enumerate() {
            self.queue.write_buffer(&self.params_buf[i], 0, bytemuck::bytes_of(p));
        }

        let ao = [
            f.proj_diag[0], f.proj_diag[1], f.near_far[0], f.near_far[1],
            35.0, 6.0, f.ao_radius, f.ao_strength,
            w as f32, h as f32, 0.0, 0.0,
        ];
        self.queue.write_buffer(&self.ao_buf, 0, bytemuck::cast_slice(&ao));

        let vbuf = |label: &str, m: &Mesh| {
            let v = if m.v.is_empty() { vec![crate::mesh::Vertex::default()] } else { m.v.clone() };
            let i = if m.i.is_empty() { vec![0u32, 0, 0] } else { m.i.clone() };
            (
                self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
                    label: Some(label),
                    contents: bytemuck::cast_slice(&v),
                    usage: wgpu::BufferUsages::VERTEX,
                }),
                self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
                    label: Some(label),
                    contents: bytemuck::cast_slice(&i),
                    usage: wgpu::BufferUsages::INDEX,
                }),
                m.i.len() as u32,
            )
        };
        let (sv, si, sn) = vbuf("solid", solid);
        let (gv, gi, gn) = vbuf("glass", glass);

        let t = self.targets.as_ref().expect("targets");
        let mut enc = self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor { label: Some("frame") });

        // 1. sun shadow map (opaque only: the glass casts none)
        {
            let mut p = enc.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("shadow"),
                color_attachments: &[],
                depth_stencil_attachment: Some(wgpu::RenderPassDepthStencilAttachment {
                    view: &self.shadow_view,
                    depth_ops: Some(wgpu::Operations { load: wgpu::LoadOp::Clear(1.0), store: wgpu::StoreOp::Store }),
                    stencil_ops: None,
                }),
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });
            p.set_pipeline(&self.shadow_pipe);
            p.set_bind_group(0, &self.bg_shadow, &[]);
            p.set_vertex_buffer(0, sv.slice(..));
            p.set_index_buffer(si.slice(..), wgpu::IndexFormat::Uint32);
            p.draw_indexed(0..sn, 0, 0..1);
        }

        // 2. the scene, 4x MSAA, resolved into the HDR target
        {
            let mut p = enc.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("scene"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &t.msaa_color,
                    depth_slice: None,
                    resolve_target: Some(&t.hdr_view),
                    ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::TRANSPARENT), store: wgpu::StoreOp::Discard },
                })],
                depth_stencil_attachment: Some(wgpu::RenderPassDepthStencilAttachment {
                    view: &t.depth,
                    depth_ops: Some(wgpu::Operations { load: wgpu::LoadOp::Clear(1.0), store: wgpu::StoreOp::Discard }),
                    stencil_ops: None,
                }),
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });
            p.set_bind_group(0, &self.bg_main, &[]);
            p.set_pipeline(&self.opaque_pipe);
            p.set_vertex_buffer(0, sv.slice(..));
            p.set_index_buffer(si.slice(..), wgpu::IndexFormat::Uint32);
            p.draw_indexed(0..sn, 0, 0..1);
            p.set_pipeline(&self.glass_pipe);
            p.set_vertex_buffer(0, gv.slice(..));
            p.set_index_buffer(gi.slice(..), wgpu::IndexFormat::Uint32);
            p.draw_indexed(0..gn, 0, 0..1);
        }

        // 2b. depth prepass (opaque, cut) for the occlusion pass
        {
            let mut p = enc.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("depth"),
                color_attachments: &[],
                depth_stencil_attachment: Some(wgpu::RenderPassDepthStencilAttachment {
                    view: &t.depth1_view,
                    depth_ops: Some(wgpu::Operations { load: wgpu::LoadOp::Clear(1.0), store: wgpu::StoreOp::Store }),
                    stencil_ops: None,
                }),
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });
            p.set_pipeline(&self.depth_pipe);
            p.set_bind_group(0, &self.bg_shadow, &[]);
            p.set_vertex_buffer(0, sv.slice(..));
            p.set_index_buffer(si.slice(..), wgpu::IndexFormat::Uint32);
            p.draw_indexed(0..sn, 0, 0..1);
        }

        // 2c. screen-space occlusion: raw samples, depth-aware blur, multiply into the scene
        let ao_pass = |enc: &mut wgpu::CommandEncoder, label: &str, pipe: &wgpu::RenderPipeline, a: &wgpu::TextureView, b: &wgpu::TextureView, dst: &wgpu::TextureView| {
            let bg = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
                label: Some(label),
                layout: &self.bgl_ao,
                entries: &[
                    wgpu::BindGroupEntry { binding: 0, resource: self.ao_buf.as_entire_binding() },
                    wgpu::BindGroupEntry { binding: 1, resource: wgpu::BindingResource::TextureView(&t.depth1_view) },
                    wgpu::BindGroupEntry { binding: 2, resource: wgpu::BindingResource::TextureView(a) },
                    wgpu::BindGroupEntry { binding: 3, resource: wgpu::BindingResource::TextureView(b) },
                ],
            });
            let mut p = enc.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some(label),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: dst,
                    depth_slice: None,
                    resolve_target: None,
                    ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::BLACK), store: wgpu::StoreOp::Store },
                })],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });
            p.set_pipeline(pipe);
            p.set_bind_group(0, &bg, &[]);
            p.draw(0..3, 0..1);
        };
        ao_pass(&mut enc, "ao raw", &self.ao_raw_pipe, &t.hdr_view, &t.hdr_view, &t.ao_raw_view);
        ao_pass(&mut enc, "ao blur", &self.ao_blur_pipe, &t.ao_raw_view, &t.hdr_view, &t.ao_blur_view);
        ao_pass(&mut enc, "ao apply", &self.ao_apply_pipe, &t.ao_blur_view, &t.hdr_view, &t.hdr2_view);

        // 3. bright pass -> half-res, blur, blur back
        let post = |enc: &mut wgpu::CommandEncoder, label: &str, pipe: &wgpu::RenderPipeline, src_a: &wgpu::TextureView, src_b: &wgpu::TextureView, dst: &wgpu::TextureView, params: &wgpu::Buffer, out_fmt_is_comp: bool| {
            let bg = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
                label: Some(label),
                layout: if out_fmt_is_comp { &self.comp_bgl } else { &self.post_bgl },
                entries: &[
                    wgpu::BindGroupEntry { binding: 0, resource: params.as_entire_binding() },
                    wgpu::BindGroupEntry { binding: 1, resource: wgpu::BindingResource::TextureView(src_a) },
                    wgpu::BindGroupEntry { binding: 2, resource: wgpu::BindingResource::TextureView(src_b) },
                    wgpu::BindGroupEntry { binding: 3, resource: wgpu::BindingResource::Sampler(&self.lin) },
                ],
            });
            let mut p = enc.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some(label),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: dst,
                    depth_slice: None,
                    resolve_target: None,
                    ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::BLACK), store: wgpu::StoreOp::Store },
                })],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });
            p.set_pipeline(pipe);
            p.set_bind_group(0, &bg, &[]);
            p.draw(0..3, 0..1);
        };
        post(&mut enc, "bright", &self.bright_pipe, &t.hdr2_view, &t.hdr2_view, &t.bloom_a, &self.params_buf[0], false);
        post(&mut enc, "blur h", &self.blur_pipe, &t.bloom_a, &t.bloom_a, &t.bloom_b, &self.params_buf[1], false);
        post(&mut enc, "blur v", &self.blur_pipe, &t.bloom_b, &t.bloom_b, &t.bloom_a, &self.params_buf[2], false);

        // 4. composite to display sRGB
        post(&mut enc, "composite", &self.comp_pipe, &t.hdr2_view, &t.bloom_a, &t.out_view, &self.params_buf[3], true);

        // 5. read back
        enc.copy_texture_to_buffer(
            wgpu::TexelCopyTextureInfo { texture: &t.out, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
            wgpu::TexelCopyBufferInfo {
                buffer: &t.read,
                layout: wgpu::TexelCopyBufferLayout { offset: 0, bytes_per_row: Some(t.padded_row), rows_per_image: Some(h) },
            },
            wgpu::Extent3d { width: w, height: h, depth_or_array_layers: 1 },
        );
        self.queue.submit(Some(enc.finish()));

        let slice = t.read.slice(..);
        slice.map_async(wgpu::MapMode::Read, |_| {});
        let _ = self.device.poll(wgpu::PollType::wait_indefinitely());
        let data = slice.get_mapped_range().unwrap();
        let mut px = Vec::with_capacity((w * h * 4) as usize);
        for row in 0..h as usize {
            let start = row * t.padded_row as usize;
            px.extend_from_slice(&data[start..start + (w * 4) as usize]);
        }
        drop(data);
        t.read.unmap();
        RgbaImage::from_raw(w, h, px).expect("frame size")
    }
}

