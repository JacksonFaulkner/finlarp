// Time helpers for scenes. Everything is a pure function of the clock, so a
// frame can be rendered at any millisecond with no state carried between
// frames (the player can skip frames, pause, or seek, and tests can sample
// any instant).

/// Deterministic 64-bit mix of two numbers (splitmix64 finalizer).
pub fn hash(a: u64, b: u64) -> u64 {
    let mut z = a
        .wrapping_mul(0x9E37_79B9_7F4A_7C15)
        .wrapping_add(b.wrapping_mul(0xD1B5_4A32_D192_ED03))
        .wrapping_add(0x1234_5678_9ABC_DEF1);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// Hash -> [0, 1).
pub fn unit(h: u64) -> f32 {
    (h >> 40) as f32 / (1u64 << 24) as f32
}

/// [0, 1) noise for a cell / particle: `noise(seed, key)`.
pub fn noise(seed: u64, key: u64) -> f32 {
    unit(hash(seed, key))
}

pub fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t
}

pub fn ease_in_out(t: f32) -> f32 {
    let t = t.clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// Pick one of `n` options that changes every `period_ms` (flicker, blink).
pub fn flicker(ms: u64, period_ms: u64, seed: u64, n: u64) -> u64 {
    hash(seed, ms / period_ms.max(1)) % n.max(1)
}

/// A stream of short-lived things (gas bubbles, sparks, smoke) emitted at a
/// steady rate. Stateless: `each` re-derives which particles are alive at
/// `now_ms` from their index, so there is nothing to update per frame.
#[derive(Debug, Clone, Copy)]
pub struct Particles {
    pub seed: u64,
    /// Average gap between spawns.
    pub every_ms: u64,
    pub life_ms: u64,
}

#[derive(Debug, Clone, Copy)]
pub struct Particle {
    pub id: u64,
    /// 0 at spawn -> 1 at death.
    pub age: f32,
    seed: u64,
}

impl Particle {
    /// Per-particle random in [0, 1); `k` picks an independent stream
    /// (one for x, one for speed, ...).
    pub fn rand(&self, k: u64) -> f32 {
        noise(self.seed ^ k.wrapping_mul(0xA24B_AED4_963E_E407), self.id)
    }
}

impl Particles {
    pub const fn new(seed: u64, every_ms: u64, life_ms: u64) -> Self {
        Self {
            seed,
            every_ms,
            life_ms,
        }
    }

    /// Calls `f` for every particle alive at `now_ms`. The stream is
    /// shifted by one lifetime so particles already exist at t = 0.
    pub fn each(&self, now_ms: u64, mut f: impl FnMut(Particle)) {
        let every = self.every_ms.max(1);
        let life = self.life_ms.max(1);
        let now = now_ms + life;
        let first = (now - life) / every;
        for id in first.saturating_sub(1)..=now / every {
            let jitter = (noise(self.seed, id) * every as f32 * 0.9) as u64;
            let spawn = id * every + jitter;
            if spawn <= now && now - spawn < life {
                f(Particle {
                    id,
                    age: (now - spawn) as f32 / life as f32,
                    seed: self.seed,
                });
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn noise_is_stable_and_in_range() {
        for k in 0..1000 {
            let n = noise(7, k);
            assert!((0.0..1.0).contains(&n));
            assert_eq!(n, noise(7, k));
        }
        assert_ne!(noise(1, 5), noise(2, 5));
    }

    #[test]
    fn easing_is_clamped() {
        assert_eq!(ease_in_out(-1.0), 0.0);
        assert_eq!(ease_in_out(2.0), 1.0);
        assert!((ease_in_out(0.5) - 0.5).abs() < 1e-6);
    }

    #[test]
    fn particles_are_alive_at_start_and_ages_are_valid() {
        let p = Particles::new(3, 200, 1000);
        let mut n = 0;
        p.each(0, |q| {
            n += 1;
            assert!((0.0..1.0).contains(&q.age));
        });
        // ~life/every particles in flight in steady state
        assert!((3..=8).contains(&n), "{n} alive at t=0");
        let (mut a, mut b) = (vec![], vec![]);
        p.each(5000, |q| a.push(q.id));
        p.each(5000, |q| b.push(q.id));
        assert_eq!(a, b, "same instant, same particles");
    }

    #[test]
    fn flicker_holds_within_a_period() {
        assert_eq!(flicker(10, 100, 1, 3), flicker(90, 100, 1, 3));
        assert!(flicker(0, 100, 1, 3) < 3);
    }
}
