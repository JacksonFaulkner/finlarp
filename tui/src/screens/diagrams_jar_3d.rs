// The Siemens bell jar as a 3D model for the full-screen view (`F`): poly3d's jar rig, keyed to the
// jar's beats. The jar's pictures themselves are the Blender scenes in diagrams_nodes/polysilicon.

use crate::ui::anim::{Time, ease_in_out};

/// The bell jar's state at `t` for the 3D view, on the same beats as the zoom: 0 evacuate,
/// 1 heat, 2 TCS flow, 3 time-lapse growth, 4 hydrogen, 5 shutdown. Growth runs over beat 3.
/// The flows are the directions of travel drawn over the scene.
pub fn bell_jar_anim(t: &Time) -> poly3d::Anim {
    let e = ease_in_out(t.local) as f64;
    let (heat, rod_d, flow) = match t.beat {
        0 => (
            0.0,
            20.0,
            poly3d::Flow {
                pump: 1.0,
                ..Default::default()
            },
        ),
        1 => (
            e,
            20.0,
            poly3d::Flow {
                power: e,
                ..Default::default()
            },
        ),
        2 => (
            1.0,
            20.0,
            poly3d::Flow {
                feed: 1.0,
                exhaust: 0.6 * e,
                power: 1.0,
                ..Default::default()
            },
        ),
        3 => (
            1.0,
            20.0 + 140.0 * e,
            poly3d::Flow {
                feed: 1.0,
                exhaust: 0.6,
                power: 1.0,
                ..Default::default()
            },
        ),
        4 => (
            1.0,
            160.0,
            poly3d::Flow {
                feed: 1.0,
                exhaust: 0.6,
                power: 1.0,
                ..Default::default()
            },
        ),
        _ => (
            1.0 - e,
            160.0,
            poly3d::Flow {
                exhaust: 0.6 * (1.0 - e),
                power: 1.0 - e,
                ..Default::default()
            },
        ),
    };
    // one dash cycle every two seconds, so the flows read as moving
    let phase = (t.ms % 2000) as f64 / 2000.0;
    poly3d::Anim {
        heat,
        rod_d,
        flow,
        phase,
    }
}
