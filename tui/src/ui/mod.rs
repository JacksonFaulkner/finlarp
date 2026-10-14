// Reusable components. Every screen is composed from these; none of them
// know which screen they're in. Components that show data take `model`
// types and always expose the Source of whatever is selected, so any
// screen gets the source bar / inspector / audit overlay for free.
//
//   theme        colours + semantic styles (from nvim's colorscheme args)
//   layout       standard screen frames (header / nav / detail / source bar)
//   block_grid   blocks as a grid of bordered containers, spatial hjkl (dashboards)
//   calendar     month / week / day views over dated events (weekends can be hidden)
//   block_view   renders model::Block lists with a row/cell cursor (Table, Kv, Series, Bars, Text)
//   section_list left nav: List + ListState over model::Section (long lists)
//   section_tabs top nav: one row of tabs over model::Section (few, short sections)
//   spacing      padding / gap tokens by screen size (theme.spacing)
//   source_bar   one-line source of the selection + SourceInspector popup (formula + inputs)
//   candles      OHLC candlestick chart with price axis + volume strip
//   charts       grouped bars, sparklines with gaps, line chart helpers
//   hcandles     horizontal candles (one row per bar) for the intraday tape
//   help         `?` keymap overlay + footer key hints
//   text         width-aware truncate / wrap, URL shortening, number formatting

// A component library: not every screen uses every helper.
#![allow(dead_code)]

pub mod block_grid;
pub mod block_view;
pub mod calendar;
pub mod candles;
pub mod charts;
pub mod command_palette;
pub mod hcandles;
pub mod help;
pub mod layout;
pub mod section_list;
pub mod section_tabs;
pub mod source_bar;
pub mod spacing;
pub mod text;
pub mod theme;
