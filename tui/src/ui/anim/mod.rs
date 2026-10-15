// Animation layer: procedural, time-driven scenes drawn on a character grid.
// A screen holds a `Player`, asks it for a `Shot` each redraw, and styles
// the lines itself. Nothing here knows about any screen.
//
//   canvas   char grid with clipped drawing (text, lines, boxes, blit)
//   motion   noise, easing, flicker, stateless Particles streams
//   shapes   Path (+ flow of particles along it), ellipses, titled boxes
//   scene    Scene trait (beats + pure draw(t)), Time, Player, Shot
//
// Writing a scene: list the beats (caption + duration), then in `draw`
// derive everything from `Time` and `motion` (no mutable state), so any
// frame can be rendered at any instant and tested without a terminal.

pub mod canvas;
pub mod motion;
pub mod scene;
pub mod shapes;

pub use canvas::Canvas;
pub use motion::{Particles, ease_in_out, flicker, lerp, noise};
pub use scene::{Beat, Player, Scene, Time, Zoom};
