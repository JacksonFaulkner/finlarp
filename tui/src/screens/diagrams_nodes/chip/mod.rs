// CHIP-tab node pages: each overview is the whole-chip Blender scene zoomed in on its part.

use super::Node;

mod contacts;
mod finfet;
mod gaa;
mod gate_stack;
mod mid_metal;
mod nmos;
mod planar;
mod pmos;
mod thin_metal;
mod top_metal;

pub const NODES: [&Node; 10] = [
    &top_metal::NODE,
    &mid_metal::NODE,
    &thin_metal::NODE,
    &contacts::NODE,
    &nmos::NODE,
    &gate_stack::NODE,
    &pmos::NODE,
    &planar::NODE,
    &finfet::NODE,
    &gaa::NODE,
];
