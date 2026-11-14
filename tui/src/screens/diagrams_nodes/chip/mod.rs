// CHIP-tab node pages: each overview is the whole-chip Blender scene zoomed in on its part.

use super::Node;

mod top_metal;
mod mid_metal;
mod thin_metal;
mod contacts;
mod nmos;
mod gate_stack;
mod pmos;
mod planar;
mod finfet;
mod gaa;

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
