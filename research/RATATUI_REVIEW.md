**Ratatui review — 2026-09-27**

Scope: the current working tree, including the existing uncommitted grid, tabs, spacing, theme, screen, and launcher changes. This is a research and code review; application code was not changed. Findings below distinguish observed code paths and test results from proposed improvements. Performance costs have not been benchmarked in a live terminal.

**How this application uses Ratatui**

`ui/portfolio_chart.lua` launches one Rust binary in a tmux popup, with a floating Neovim terminal fallback. `main.rs` selects chart, CANSLIM, dossier, or search. Python services produce data; Rust reads cached data from DuckDB. Search runs its Python client through background communication and applies replies in `tick()`. Browser and clipboard actions stay in the application; document viewing and screen changes return JSON to Neovim and exit.

`app.rs` owns terminal lifecycle through `ratatui::run`, catches Crossterm events, calls screen handlers, and dispatches actions. Screens compose shared frame/layout helpers, semantic theme styles, navigation, block renderers, source bars, inspectors, and help. `BlockView` renders a vertical document; the new `BlockGrid` adds dashboard packing and spatial navigation. Selection ties the visible value to its source or derivation. Keep that relationship central to future changes.

The lockfile already uses Ratatui **0.30.2** and tui-input **0.15.5**. Existing code uses contemporary features: merged borders, overlapping layout, stateful lists/tables, custom widgets, chart markers, and missing-data gaps. The existing screen/component split fits Ratatui's documented [component architecture](https://ratatui.rs/concepts/application-patterns/component-architecture/) and [custom-widget model](https://ratatui.rs/recipes/widgets/custom/).

Ratatui reconstructs the frame in memory and diffs it against the previous frame before terminal output. Every actual draw must describe the complete visible UI. The diff saves terminal writes; it does not remove application allocations, cloning, text measurement, or widget rendering. This distinction matters for the performance findings below. [Rendering internals](https://ratatui.rs/concepts/rendering/under-the-hood/).

**Recommended work, in order**

1. **Make focus and event routing match what is visible.**

   In `screens/search/view.rs`, facets disappear below 90 columns. In `screens/search/mod.rs:82`, `Pane::cycle` still cycles through all four panes. Tab can therefore focus an invisible facets list; resizing while facets has focus has the same problem. Compute visible panes with layout, cycle only those panes, and move focus when its pane disappears. A compact facets overlay would preserve filtering on small screens.

   In `screens/dossier.rs:362`, top-level `h/l` handlers switch panes before `BlockView::on_key` can select table columns. Tab and Escape are similarly intercepted before the block's corresponding handlers. Use an explicit routing order: global exit, active overlay/input mode, focused component, then unhandled screen navigation. Decide which keys belong to each level and make help reflect that choice. Ratatui provides rendering, while this event policy belongs to the application. [Event handling patterns](https://ratatui.rs/concepts/event-handling/).

   Validate at screen level: narrow-screen Tab traversal, focus repair after resize, and table column selection through the dossier handler. Component-only tests cannot catch parent interception.

2. **Correct Unicode input rendering and support paste deliberately.**

   `screens/search/view.rs:125` uses `value.chars().skip(scroll)`, where `scroll` comes from `Input::visual_scroll`. That offset measures terminal display columns, not Unicode scalar values. Wide characters and combining sequences can make the visible text disagree with the cursor. This is confirmed by the locally installed tui-input 0.15.5 source and its Ratatui example, as well as the [Input API](https://docs.rs/tui-input/latest/tui_input/struct.Input.html).

   Render the input in a separate rectangle using `Paragraph::scroll((0, scroll))`, following the [upstream example](https://github.com/sayanarijit/tui-input/blob/main/examples/ratatui_crossterm_input.rs). Keep prompt and status outside the scrolling rectangle. Guard cursor placement when that rectangle is empty. Add cases for CJK, combining accents, emoji, and narrow input widths.

   The runtime currently discards `Event::Paste`; bracketed paste also needs explicit terminal setup and cleanup. Support it as one input edit/debounce operation. Review the global `?` binding too: it opens help even while typing a query. [Ratatui user-input example](https://ratatui.rs/examples/apps/user_input/) and [full event-handling tutorial](https://ratatui.rs/tutorials/counter-async-app/full-async-events/) provide relevant patterns.

3. **Make updates explicitly request redraws.**

   `Screen::needs_redraw` defaults to true (`app.rs:89`). CANSLIM, dossier, and search inherit it, so idle polling rebuilds their screens roughly every 100 ms. CANSLIM clones its scorecard in `draw`; dossier clones its document; navigation clones block collections. Search rebuilds result snippets and clones/wraps preview content. Chart already suppresses idle redraws except while a flash is active.

   Give update/tick results an explicit changed flag, process completed work before drawing, and render when state changed. Set static screens to idle without redraws. Search cannot simply return false from `needs_redraw`: incoming replies and expired flashes currently mutate state while `tick()` returns `Action::None`. Those changes must invalidate the frame. The current draw-before-tick order also lets a received result wait through the following poll before it appears.

   Start with this small runtime change and disjoint field borrows. Cache expensive wrapping/measurement only after profiling. Existing background workers can remain; Ratatui's [FAQ](https://ratatui.rs/faq/) makes async adoption dependent on application needs, and its [async tutorial](https://ratatui.rs/tutorials/counter-async-app/full-async-events/) separates updates from rendering.

4. **Render grid content in proportion to the viewport.**

   `ui/block_grid.rs:330` allocates a buffer for the entire virtual page and renders every container. `draw_container` then allocates another buffer for each block's full body before copying its visible rows. Scrolling a dashboard pays for offscreen containers too. `BlockView` already skips wholly offscreen blocks, although each intersecting block still gets a full-height temporary buffer.

   First skip nonintersecting grid containers. Then measure and render visible row ranges into bounded buffers, preserving merged edges and selected-row expansion. Keep logical document offsets in a wider type; convert to terminal coordinates only for visible rectangles. Benchmark large fixtures before and after, including allocation counts and key-to-frame latency. This is a demonstrated work pattern, not a measured claim of user-visible lag.

5. **Separate compact spacing from column count.**

   `Spacing::for_area` makes any terminal shorter than 30 rows Compact. `GridView` then maps Compact to one column. A wide 180×24 popup therefore becomes a single long column despite ample horizontal room. Determine grid columns from available width and block minimum widths; let height affect padding and card height independently.

   CANSLIM calls `theme.fit(area)`, but dossier and search do not, so shared spacing policy is not consistently applied. Use one layout result that describes pane visibility, density, minimum useful content areas, and focus order. Dossier currently reserves at least 12 columns for navigation even at tiny widths. At short heights, consider a selected-pane view and compact source summary. [Layout concepts](https://ratatui.rs/concepts/layout/) and [dynamic layouts](https://ratatui.rs/recipes/layout/dynamic/) support deriving constraints from size and state; exact breakpoints remain a product decision.

6. **Give the grid a clear border and title contract.**

   Shared frame rendering already uses the documented overlap/merge approach. Keep it. `BlockGrid::render_in_frame`, however, expands an inner rectangle, overwrites the surrounding detail border/title, then rewrites corner glyphs. The CANSLIM test output shows the consequence: the full selected section title disappears while its tab is truncated.

   Let a frame explicitly return an outer grid area whose borders the grid owns, with a dedicated place for the selected section's full title. Keep compact tab labels/badges for overview and the full active title for orientation. Prefer passing geometry over reconstructing it from an inner rectangle. [Collapsed-border recipe](https://ratatui.rs/recipes/layout/collapse-borders/).

7. **Complete theme inheritance.**

   The launcher supplies background, positive/negative colors, and CursorLine background. `Theme::from_args` retains default white foreground, dark-gray dim/border, and a fixed accent. The claimed colorscheme integration is therefore partial, especially for light themes.

   Pass Normal foreground and appropriate muted, border, and accent highlights through the same bridge. Check contrast in light, dark, and transparent themes; add direct cell-style assertions for selection and focus. Preserve numeric sign and labels alongside color. The chart already exposes marker switching; retain that because Ratatui documents weaker font support for Sextant/Octant characters. [0.30 release notes](https://ratatui.rs/highlights/v030/).

8. **Extend existing tests to cover interactions and visual contracts.**

   `cargo test --locked --offline --quiet` ran 87 tests: **86 passed, 1 failed**. The failure is `screens::canslim::tests::renders_header_nav_and_rule`, at `canslim.rs:396`: it expects `Current earnings`, while the 160×48 frame shows `C Current ear…` and grid card titles replace the detail title. Resolve whether the selected title should remain fully visible before changing the assertion.

   Existing fixture, source, tiny-size, event-loop, debounce, and stale-reply tests are useful. Add selected full-frame snapshots at 80×24, 120×30, 160×48, and 180×24; then test resize while focused, overlay dismissal, long-row navigation, Unicode input, and background replies through the runtime. Keep style checks alongside snapshots, because plain text snapshots omit color. [Snapshot testing recipe](https://ratatui.rs/recipes/testing/snapshots/).

   Add a small terminal integration check for tmux and Neovim handoff when changing the launcher. `ensure_built()` currently blocks Neovim with `vim.fn.system`; after a failed build it can still launch an older executable. An asynchronous build with an explicit success result would improve the development loop.

**Additional research context**

The [0.30.2 release notes](https://ratatui.rs/highlights/v0302/) cover wide-cell cleanup and scrollbar fixes; the project already has that version. The [table example](https://ratatui.rs/examples/widgets/table/) is relevant for retained selection state, and the [panic example](https://ratatui.rs/examples/apps/panic/) confirms that modern initialization installs terminal-restoring panic handling. The existing runtime and overlays already address much of this foundation.

Suggested first implementation slice: repair the selected CANSLIM title/test contract, hidden-pane focus, dossier key routing, and Unicode input; then add explicit redraw invalidation. Follow with viewport rendering and the responsive layout/theme work, using measurements and snapshots to evaluate the changes.
