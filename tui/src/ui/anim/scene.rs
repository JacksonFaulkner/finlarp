// Scene = a looping sequence of captioned beats drawn onto a Canvas as a
// pure function of time. Player owns the clock and turns a Scene into
// text frames any screen can style and show.

use std::time::Instant;

use super::canvas::Canvas;

/// One captioned stretch of a scene's loop.
#[derive(Debug, Clone, Copy)]
pub struct Beat {
    pub caption: &'static str,
    pub ms: u64,
    /// Side-panel text: the mechanism at this moment, and what to watch.
    pub what: &'static str,
    pub look: &'static str,
}

impl Beat {
    pub const fn new(caption: &'static str, ms: u64) -> Self {
        Self {
            caption,
            ms,
            what: "",
            look: "",
        }
    }

    pub const fn note(mut self, what: &'static str, look: &'static str) -> Self {
        self.what = what;
        self.look = look;
        self
    }
}

/// Where the loop is when a frame is drawn.
#[derive(Debug, Clone, Copy)]
pub struct Time {
    /// Milliseconds into the loop.
    pub ms: u64,
    /// Current beat index and how far through it (0..1).
    pub beat: usize,
    pub local: f32,
    /// Loop-time at which the current beat began.
    pub beat_start: u64,
}

/// A deeper look at part of a scene: its own full-size scene, opened from
/// the parent's menu.
#[derive(Clone, Copy)]
pub struct Zoom {
    /// Key shown in the menu (a, b, c...) and the name of the zoom.
    pub key: char,
    pub label: &'static str,
    pub build: fn() -> Box<dyn Scene>,
}

pub trait Scene {
    /// Canvas columns, rows. Fixed, so the popup layout never jumps.
    fn size(&self) -> (u16, u16);
    fn beats(&self) -> &[Beat];
    /// Draw the frame for `t` onto a cleared canvas.
    fn draw(&self, c: &mut Canvas, t: &Time);
    /// Parts worth a closer look, each its own scene.
    fn zooms(&self) -> &[Zoom] {
        &[]
    }
}

/// One rendered frame.
#[derive(Debug, Clone)]
pub struct Shot {
    pub beat: usize,
    pub beats: usize,
    pub caption: &'static str,
    pub what: &'static str,
    pub look: &'static str,
    pub lines: Vec<String>,
}

pub struct Player {
    scene: Box<dyn Scene>,
    /// Loop position (ms) as of `since`; frozen while `paused`.
    base: u64,
    since: Instant,
    paused: bool,
    total: u64,
    canvas: Canvas,
}

impl Player {
    pub fn new(scene: Box<dyn Scene>, start: Instant) -> Self {
        let (w, h) = scene.size();
        let total = scene
            .beats()
            .iter()
            .map(|b| b.ms.max(1))
            .sum::<u64>()
            .max(1);
        Self {
            scene,
            base: start.elapsed().as_millis() as u64,
            since: Instant::now(),
            paused: false,
            total,
            canvas: Canvas::new(w, h),
        }
    }

    /// Canvas rows (frames are always this tall).
    pub fn height(&self) -> usize {
        self.canvas.height()
    }

    /// Resize the canvas to the room available (never below the scene's own
    /// size); scenes lay themselves out from the canvas they are given.
    pub fn fit(&mut self, w: u16, h: u16) {
        let (mw, mh) = self.scene.size();
        let (w, h) = (w.max(mw) as usize, h.max(mh) as usize);
        if (w, h) != (self.canvas.width(), self.canvas.height()) {
            self.canvas = Canvas::new(w as u16, h as u16);
        }
    }

    /// The scene's own (minimum) size.
    pub fn min_size(&self) -> (u16, u16) {
        self.scene.size()
    }

    pub fn zooms(&self) -> &[Zoom] {
        self.scene.zooms()
    }

    /// Canvas columns.
    pub fn width(&self) -> usize {
        self.canvas.width()
    }

    /// Length of one loop.
    pub fn loop_ms(&self) -> u64 {
        self.total
    }

    pub fn time_at(&self, ms: u64) -> Time {
        let ms = ms % self.total;
        let mut start = 0;
        let beats = self.scene.beats();
        for (i, b) in beats.iter().enumerate() {
            let len = b.ms.max(1);
            if ms < start + len || i + 1 == beats.len() {
                return Time {
                    ms,
                    beat: i,
                    local: ((ms - start) as f32 / len as f32).clamp(0.0, 1.0),
                    beat_start: start,
                };
            }
            start += len;
        }
        Time {
            ms,
            beat: 0,
            local: 0.0,
            beat_start: 0,
        }
    }

    pub fn shot_at(&mut self, ms: u64) -> Shot {
        let t = self.time_at(ms);
        self.canvas.clear();
        self.scene.draw(&mut self.canvas, &t);
        let beats = self.scene.beats();
        Shot {
            beat: t.beat,
            beats: beats.len(),
            caption: beats.get(t.beat).map_or("", |b| b.caption),
            what: beats.get(t.beat).map_or("", |b| b.what),
            look: beats.get(t.beat).map_or("", |b| b.look),
            lines: self.canvas.lines(),
        }
    }

    /// Where the loop is right now, in ms (frozen while paused).
    pub fn now_ms(&self) -> u64 {
        if self.paused {
            self.base
        } else {
            self.base + self.since.elapsed().as_millis() as u64
        }
    }

    /// The frame for right now.
    pub fn shot(&mut self) -> Shot {
        self.shot_at(self.now_ms())
    }

    pub fn is_paused(&self) -> bool {
        self.paused
    }

    /// Freeze the frame, or carry on from where it stopped.
    pub fn toggle_pause(&mut self) {
        self.base = self.now_ms();
        self.since = Instant::now();
        self.paused = !self.paused;
    }

    /// Jump to `ms` into the loop (wraps).
    pub fn seek(&mut self, ms: u64) {
        self.base = ms % self.total;
        self.since = Instant::now();
    }

    /// Jump to the start of the next (`+1`) or previous (`-1`) beat.
    pub fn step_beat(&mut self, delta: i32) {
        let n = self.scene.beats().len() as i32;
        if n == 0 {
            return;
        }
        let cur = self.time_at(self.now_ms()).beat as i32;
        let to = (cur + delta).rem_euclid(n) as usize;
        let start: u64 = self.scene.beats()[..to].iter().map(|b| b.ms.max(1)).sum();
        self.seek(start);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct Two;
    const BEATS: &[Beat] = &[Beat::new("a", 100), Beat::new("b", 300)];
    impl Scene for Two {
        fn size(&self) -> (u16, u16) {
            (6, 2)
        }
        fn beats(&self) -> &[Beat] {
            BEATS
        }
        fn draw(&self, c: &mut Canvas, t: &Time) {
            c.text(0, 0, &format!("{}", t.beat));
            c.text(0, 1, &format!("{:.2}", t.local));
        }
    }

    #[test]
    fn pause_freezes_the_clock_and_resume_continues() {
        let mut p = Player::new(Box::new(Two), Instant::now());
        p.seek(50);
        p.toggle_pause();
        assert!(p.is_paused());
        let a = p.shot().lines;
        std::thread::sleep(std::time::Duration::from_millis(30));
        assert_eq!(p.shot().lines, a);
        assert_eq!(p.now_ms(), 50);
        p.toggle_pause();
        std::thread::sleep(std::time::Duration::from_millis(25));
        assert!(p.now_ms() >= 70 && !p.is_paused());
    }

    #[test]
    fn step_beat_jumps_between_beat_starts_and_wraps() {
        let mut p = Player::new(Box::new(Two), Instant::now());
        p.seek(10);
        p.toggle_pause();
        p.step_beat(1);
        assert_eq!(p.now_ms(), 100);
        p.step_beat(1);
        assert_eq!(p.now_ms(), 0, "wraps to the first beat");
        p.step_beat(-1);
        assert_eq!(p.now_ms(), 100, "wraps back");
    }

    #[test]
    fn fit_grows_the_canvas_but_not_below_the_scene_size() {
        let mut p = Player::new(Box::new(Two), Instant::now());
        p.fit(20, 9);
        assert_eq!((p.width(), p.height()), (20, 9));
        assert_eq!(p.shot_at(0).lines.len(), 9);
        p.fit(1, 1);
        assert_eq!((p.width(), p.height()), (6, 2));
    }

    #[test]
    fn beats_loop_and_report_progress() {
        let mut p = Player::new(Box::new(Two), Instant::now());
        assert_eq!(p.loop_ms(), 400);
        let s = p.shot_at(0);
        assert_eq!((s.beat, s.caption), (0, "a"));
        let s = p.shot_at(250);
        assert_eq!((s.beat, s.caption, s.beats), (1, "b", 2));
        assert_eq!(s.lines[1], "0.50");
        let s = p.shot_at(400 + 50);
        assert_eq!(s.beat, 0, "wraps");
        assert_eq!(s.lines[1], "0.50");
        assert_eq!(p.time_at(250).beat_start, 100);
    }
}
