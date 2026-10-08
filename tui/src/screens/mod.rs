// One module per screen. Each exposes `open(ctx, arg) -> io::Result<impl Screen>`
// and composes src/ui components; screens hold state + key handling only.

pub mod canslim;
pub mod chart;
pub mod dossier;
pub mod earnings_report;
pub mod home;
pub mod pick;
pub mod portfolio;
pub mod search;
pub mod universe;
