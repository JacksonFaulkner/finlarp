// One module per screen. Each exposes `open(ctx, arg) -> io::Result<impl Screen>`
// and composes src/ui components; screens hold state + key handling only.

pub mod candles;
pub mod canslim;
pub mod catalyst_page;
pub mod chart;
pub mod chat;
pub mod diagrams;
mod diagrams_anim;
mod diagrams_art;
mod diagrams_cards;
mod diagrams_desc;
mod diagrams_mol;
mod diagrams_vis;
mod diagrams_vis_a;
mod diagrams_vis_b;
mod diagrams_vis_c;
mod diagrams_vis_d;
mod diagrams_vis_e;
pub mod dossier;
pub mod earnings_report;
pub mod events;
pub mod godel;
pub mod home;
pub mod intraday;
pub mod menu;
pub mod notes;
pub mod pick;
pub mod portfolio;
pub mod search;
pub mod universe;
