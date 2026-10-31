//! Eased rotation for a spinning pie. `tick` chases a target angle with an
//! exponential ease-out; the owner redraws at `FRAME` while `turning`.

use std::time::{Duration, Instant};

/// Redraw interval while a pie is turning.
pub const FRAME: Duration = Duration::from_millis(16);
/// Ease-out time constant (s).
const TAU: f64 = 0.09;

pub struct Spin {
    /// Current rotation in degrees, clockwise.
    pub angle: f64,
    /// Still chasing the target: redraw at `FRAME`.
    pub turning: bool,
    at: Instant,
}

impl Default for Spin {
    fn default() -> Self {
        Self {
            angle: 0.0,
            turning: false,
            at: Instant::now(),
        }
    }
}

impl Spin {
    /// Move toward `target` degrees, the short way round. `live` is false
    /// when the pie is not on screen: it snaps instead of turning.
    pub fn tick(&mut self, target: f64, live: bool, now: Instant) {
        let dt = now.duration_since(self.at).as_secs_f64().min(0.1);
        self.at = now;
        let delta = (target - self.angle + 540.0).rem_euclid(360.0) - 180.0;
        if !live || delta.abs() < 0.2 {
            self.angle = target;
            self.turning = false;
        } else {
            self.angle += delta * (1.0 - (-dt / TAU).exp());
            self.turning = true;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn settles_on_target_and_stops_turning() {
        let mut s = Spin::default();
        s.tick(90.0, true, Instant::now());
        assert!(s.turning);
        for _ in 0..2000 {
            std::thread::sleep(Duration::from_millis(1));
            s.tick(90.0, true, Instant::now());
            if !s.turning {
                break;
            }
        }
        assert!(!s.turning);
        assert!((s.angle - 90.0).abs() < 1e-9);
    }

    #[test]
    fn off_screen_snaps_to_target() {
        let mut s = Spin::default();
        s.tick(180.0, false, Instant::now());
        assert!(!s.turning);
        assert_eq!(s.angle, 180.0);
    }
}
