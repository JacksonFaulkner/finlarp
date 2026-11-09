//! Per-frame cost counters for the rasterizer, so a slow scene can say *why* it is slow.
//!
//! Always on and cheap: a handful of thread-local adds per triangle and per line, and four
//! `Instant::now()` calls per frame. The renderers do not change to use it: the shared
//! chokepoints (`rasterize`, `Canvas::fill_tri`, `Canvas::line`, `Canvas::overlay`,
//! `to_image`) record into it. A caller brackets one frame with `begin()` and `take()`:
//!
//! ```ignore
//! poly3d::prof::begin();
//! let img = poly3d::render_zoom(z, beat, local, &view, w, h, bg);
//! let s = poly3d::prof::take();   // s.total_ms(), s.tris, s.px_tested, ...
//! ```
//!
//! What each number points at when it is large:
//! - `tris`             the scene builds too many triangles: lower `seg` on tubes/spheres,
//!                      merge boxes, skip parts that are off screen or fully transparent
//! - `px_tested`        big triangles or many overlapping ones: the bounding-box walk in
//!                      `fill_tri` touches every pixel of every triangle's box
//! - `overdraw`         `px_written / px_shaded_unique`: >3 means many hidden layers drawn
//! - `line_px`          glass wireframes / flow dashes: lots of long alpha lines
//! - `dot_px`           glowing particles (`stage::dot`), each a square of sqrt() per pixel
//! - `build_ms`         the scene's own solids() code (before the first triangle draws)
//! - `overlay_ms`       everything drawn after the solids: glass, dots, labels, callouts

use std::cell::RefCell;
use std::time::Instant;

#[derive(Clone, Copy, Debug, Default)]
pub struct Stats {
    /// triangles handed to the rasterizer
    pub tris: u64,
    /// of those, how many reached pixel work (not behind the camera, not degenerate, on screen)
    pub tris_drawn: u64,
    /// pixels visited in triangle bounding boxes
    pub px_tested: u64,
    /// pixels that passed the depth test and were written
    pub px_written: u64,
    /// pixels stepped by depth-tested and overlay lines
    pub line_px: u64,
    /// pixels visited by glowing dots
    pub dot_px: u64,
    /// lines requested (each is a projection + a DDA walk)
    pub lines: u64,
    pub build_ms: f64,
    pub sort_ms: f64,
    pub raster_ms: f64,
    pub overlay_ms: f64,
    pub image_ms: f64,
    /// image size
    pub w: u32,
    pub h: u32,
}

impl Stats {
    pub fn total_ms(&self) -> f64 {
        self.build_ms + self.sort_ms + self.raster_ms + self.overlay_ms + self.image_ms
    }
    /// Pixel writes per screen pixel: >1 means hidden surfaces drawn and then covered.
    pub fn overdraw(&self) -> f64 {
        let px = (self.w as f64 * self.h as f64).max(1.0);
        self.px_written as f64 / px
    }
    /// Running sum, for averaging over several frames.
    pub fn add(&mut self, o: &Stats) {
        self.tris += o.tris;
        self.tris_drawn += o.tris_drawn;
        self.px_tested += o.px_tested;
        self.px_written += o.px_written;
        self.line_px += o.line_px;
        self.dot_px += o.dot_px;
        self.lines += o.lines;
        self.build_ms += o.build_ms;
        self.sort_ms += o.sort_ms;
        self.raster_ms += o.raster_ms;
        self.overlay_ms += o.overlay_ms;
        self.image_ms += o.image_ms;
        self.w = o.w;
        self.h = o.h;
    }
    pub fn scaled(&self, k: f64) -> Stats {
        let f = |x: u64| (x as f64 * k).round() as u64;
        Stats {
            tris: f(self.tris),
            tris_drawn: f(self.tris_drawn),
            px_tested: f(self.px_tested),
            px_written: f(self.px_written),
            line_px: f(self.line_px),
            dot_px: f(self.dot_px),
            lines: f(self.lines),
            build_ms: self.build_ms * k,
            sort_ms: self.sort_ms * k,
            raster_ms: self.raster_ms * k,
            overlay_ms: self.overlay_ms * k,
            image_ms: self.image_ms * k,
            w: self.w,
            h: self.h,
        }
    }
}

#[derive(Default)]
struct State {
    s: Stats,
    start: Option<Instant>,
    raster_start: Option<Instant>,
    raster_end: Option<Instant>,
    image_start: Option<Instant>,
}

thread_local! {
    static ST: RefCell<State> = RefCell::new(State::default());
}

fn ms(a: Instant, b: Instant) -> f64 {
    b.saturating_duration_since(a).as_secs_f64() * 1e3
}

/// Start measuring one frame on this thread. Clears the previous frame's numbers.
pub fn begin() {
    ST.with(|st| {
        *st.borrow_mut() = State { start: Some(Instant::now()), ..State::default() };
    });
}

/// End the frame started by `begin()` and return its numbers.
pub fn take() -> Stats {
    let end = Instant::now();
    ST.with(|st| {
        let st = std::mem::take(&mut *st.borrow_mut());
        let mut s = st.s;
        let start = st.start.unwrap_or(end);
        let rs = st.raster_start.unwrap_or(start);
        let re = st.raster_end.unwrap_or(rs);
        let is = st.image_start.unwrap_or(end);
        s.build_ms = ms(start, rs);
        s.overlay_ms = ms(re, is);
        s.image_ms = ms(is, end);
        s
    })
}

pub(crate) fn with(f: impl FnOnce(&mut Stats)) {
    ST.with(|st| f(&mut st.borrow_mut().s));
}

pub(crate) fn raster_start() {
    ST.with(|st| {
        let mut st = st.borrow_mut();
        // a frame can rasterize more than once (layers); keep the first start
        if st.raster_start.is_none() {
            st.raster_start = Some(Instant::now());
        }
    });
}

pub(crate) fn raster_end(sort_ms: f64, raster_ms: f64) {
    ST.with(|st| {
        let mut st = st.borrow_mut();
        st.raster_end = Some(Instant::now());
        st.s.sort_ms += sort_ms;
        st.s.raster_ms += raster_ms;
    });
}

pub(crate) fn image_start(w: usize, h: usize) {
    ST.with(|st| {
        let mut st = st.borrow_mut();
        st.image_start = Some(Instant::now());
        st.s.w = w as u32;
        st.s.h = h as u32;
    });
}
