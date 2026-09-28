# portfolio_chart architecture

One ratatui binary, several screens, one DuckDB file, launched by
`ui/portfolio_chart.lua`. Python services write the data; this crate reads it.

```
portfolio_chart <bg> <fg_up> <fg_down> [chart|canslim|dossier|search] [arg]
```

Colours are `#rrggbb` from the colorscheme (`""` = terminal default).
Env: `SECURITY_SPREAD_DB` (DuckDB path), `SECURITY_SPREAD_ACTION_FILE` (handoff).
## Layout

`main.rs` parses the CLI into `Ctx` and dispatches; `app.rs` holds the
`Screen` trait, actions and event loop; `model.rs` the data; `ui/*` the
screen-agnostic components; `screens/*` state, keys and composition only.
## Rule: every value carries a Source

A number never reaches the screen without the place it came from.

- **Document value:** `Source::url(label, url)`. The URL may end in
  `#:~:text=<quote>`, which is what `v` jumps to in the nvim docview.
- **Computed value:** `Source::derived(label, formula, inputs)`. The formula
  is written out with its operands filled in, e.g.
  `($55,267.58 / $40,169.70 - 1) × 100 = +37.59%`. `inputs` holds the Source
  of each operand, and inputs can nest.

A value without a Source is a producer bug; renderers never invent one. A
missing observation is `None`, drawn as a gap, never as zero.

## Component model

```
Source ──► Block ──► Section ──► screen
            │           │
            │           └─ SectionList (left nav, badge / ● new marker)
            └─ BlockView (cursor over rows / points / bars)
                  └─ selected_source() ──► SourceBar (one line)
                                           SourceInspector (`i`: formula + inputs, drillable)
                                           source_action (↵ browser, v nvim, y copy)
```

- **`model::Block`**: `Table | Kv | Series | Bars | Text`; every row, point
  and bar has its own `src`. `Block::source(i)` maps a cursor to a Source.
- **`model::Section`**: titled blocks, one nav entry. `sources()` feeds the
  audit views, which regroup values by document.
- **`ui::layout`**: `render_frame` draws the standard frame with merged
  borders and returns inner areas; `panes` splits without borders.
- **`ui::charts`**: `GroupedBars`, `SparkBars`, `LineChart` (Widgets + `fn`s).
- **`ui::help`**: one `const KEYS: &[Key]` feeds the footer and `?` overlay.
- **`ui::theme`**: the only source of colours, as semantic styles.
- **`ui::text`**: width-aware truncate / wrap / fit, `short_url`, `fmt_num`.

## Screen trait and actions

```rust
pub trait Screen {
    fn draw(&mut self, frame: &mut Frame);
    fn on_key(&mut self, key: KeyEvent) -> Action;
    fn tick(&mut self) -> Action { Action::None }        // debounce / async polling
    fn set_flash(&mut self, _msg: String) {}             // "copied", "opened in browser"
    fn needs_redraw(&self) -> bool { true }              // idle-poll redraw?
}
```

`app::run` wraps the loop in `ratatui::run` (init + restore; init's panic
hook restores the terminal). Each iteration:

1. **Draw**, only after a key, resize, non-None action or flash, or when
   `needs_redraw()` is true. The default is true so tick-driven screens
   (search) keep working; key-driven screens return false, or true only
   while a flash shows (chart).
2. **Tick**, then **poll** up to 100 ms. Key presses go to `on_key`
   (Ctrl-C always quits), `Resize` forces a redraw, other events are ignored.
3. **Handle the `Action`.** `Quit` / `Exit(code)` return the code.
   `OpenBrowser` / `Copy` run in-process, then `set_flash`; the screen stays
   open. `Nvim(..)` writes the handoff (next section) and exits 0.

## nvim handoff protocol

The binary runs outside nvim and can't call it. Instead it writes **one
JSON line** to `$SECURITY_SPREAD_ACTION_FILE` and exits:

```json
{"action":"docview","url":"https://…","quote":"net revenue"}   // quote may be null
{"action":"chunk","id":"123"}
{"action":"screen","screen":"dossier","arg":"MRVL"}           // arg may be null
{"action":"picker","screen":"canslim"}
```

`ui/portfolio_chart.lua` `M.open_screen(screen, arg, {title, on_exit})`:

1. Creates a temp action file and puts the env vars on the command line
   (a tmux popup's shell gets the server's environment, not the job's).
2. **In tmux:** `jobstart{"tmux","display-popup","-E",…}` without `detach`.
   `display-popup -E` blocks until the popup closes and exits with the
   binary's code (tested on tmux 3.6), so the job's `on_exit` fires then.
   **Outside tmux:** a floating `jobstart(cmd, {term = true})`; `TermClose`
   closes the window and reads `v:event.status`.
3. On exit it calls `opts.on_exit(code, action)`, then exit code `90`
   (legacy) runs `pick_<screen>()` and anything else runs `M.dispatch(action)`:

| action | nvim side |
|---|---|
| `docview` | `ui.docview.open(url, quote)` |
| `chunk` | `ui.search.open_chunk(id)` |
| `screen` | `canslim` → `init.show_canslim`, `dossier` → `init.show_dossier`, `search` → `ui.search.pick_tui`, `chart` → `show` |
| `picker` | `init.pick_<screen>()` |

Targets are called through `pcall`; a missing one notifies instead of
erroring. `app::tests::nvim_action_json_shape` pins the JSON: change the
enum and the Lua dispatcher together.

## Adding a screen

1. `src/screens/<name>.rs` (or `<name>/mod.rs`) exposing
   `pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<impl Screen>`.
   A missing cache becomes an in-screen message, never a panic.
2. Compose `layout::render_frame`, `SectionList`, `BlockView`,
   `render_source_bar`, `SourceInspector` and `help`; one `const KEYS`;
   `source_action` as the fallthrough for ↵ / v / y.
3. Register in `screens/mod.rs`, `SCREENS` + `match` in `main.rs`, and the
   `screens` table in `ui/portfolio_chart.lua`. Add TestBackend tests.

## Adding a block type

1. Add a `model::Block` variant (serde `type` tag, lowercase); every item
   gets a `src: Option<Source>`.
2. Extend `Block::title` / `len` / `source`: all the cursor and audit need.
3. Render it in `ui/block_view.rs` (reuse `ui::charts`) and emit the same
   JSON shape from the Python producer (`views/dossier.py`, `canslim.py`).

## Testing

- **Render tests** draw into a `TestBackend` buffer and assert on its text.
  Screens load JSON fixtures (`src/screens/fixtures/*.json`,
  `search/fixture.json`) via `include_str!`; chart builds synthetic history.
  Include tiny sizes: a render must never panic.
- **Event loop tests** (`app.rs`) drive `event_loop` with a scripted
  `Events` source: redraw skipping, resize, Ctrl-C, exit codes, key release.
- **Visual check:** release binary in a detached tmux session:
  ```
  tmux new-session -d -s c5 -x 160 -y 40 'cargo run --release -- "" "" "" chart'
  tmux capture-pane -p -t c5      # -e keeps colours
  tmux send-keys -t c5 h
  ```
- **Lua launcher:** `nvim --headless` with `TMUX` pointed at a scratch tmux
  server that has a client attached; swap `binary_path` for a fake script
  that writes an action file or exits 90, and assert `on_exit` / `dispatch`.
