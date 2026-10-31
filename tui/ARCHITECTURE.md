# finlarp TUI architecture

One ratatui binary (`fl`), several screens, one DuckDB file, run from a
terminal. Python services write the data; this crate reads it and runs some
of those Python scripts itself (`pyrun.rs`) when a screen needs them.

```
fl [--bg #rrggbb] [--up #rrggbb] [--down #rrggbb] [screen] [arg]
```

No screen (or `.`) opens the home menu. The rest of the command line after the
screen name is its argument, so `fl search t:MRVL guidance` works unquoted.
Colours are optional `#rrggbb`; unset or empty means the terminal default.

Env:
- `FINLARP_DB`: DuckDB path. Default `<repo>/data/finlarp.duckdb`.
- `FINLARP_PLUGIN_DIR`: repo root for the Python calls. Default: the crate's parent directory.
- `FINLARP_PYTHON`: interpreter for the Python calls. Default `<repo>/.venv/bin/python`, else `python3` on PATH.

On start `fl` changes its working directory to `~/code/github_repos/finlarp`
when that directory exists, so Claude and the Python calls run in the repo.

## Layout

`main.rs` parses the CLI into `Ctx` and dispatches; `app.rs` holds the
`Screen` trait, actions and event loop; `model.rs` the data; `ui/*` the
screen-agnostic components; `screens/*` state, keys and composition only.

## Rule: every value carries a Source

A number never reaches the screen without the place it came from.

- **Document value:** `Source::url(label, url)`. The URL may end in
  `#:~:text=<quote>`. `↵` opens the full URL, so a browser that supports text
  fragments jumps to the quote; `v` opens it without the fragment.
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
                                           source_action (↵ browser, v browser without quote, y copy)
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
3. **Handle the `Action`** (table below).

| `Action` | What happens |
|---|---|
| `Quit` | the screen returns exit code 0 |
| `OpenBrowser(url)` | opened with the OS handler in-process; the screen stays open |
| `Copy(text)` | copied to the clipboard in-process; the screen stays open |
| `Route(Screen \| Picker)` | the screen exits with a handoff; `main` opens the requested screen |
| `Route(Claude { text })` | the Claude popup opens (below); the screen stays open |

## Screen routing

`main.rs` `run_session` keeps a stack of screens. A screen that exits with a
`Screen` or `Picker` handoff pushes the requested screen, and a picker is
replaced by its pick. A screen that quits with no handoff is popped, so `q` /
`Esc` returns to the one beneath it. The process exits when the stack is empty
or the exit code is non-zero. Errors go to stderr with exit code 1.

While it runs inside tmux, `main` sets the window name to the current screen
(`tmux_title.rs`) and restores the old name on exit.

Routing is all in-process: nothing is written to a file for another program to read.

## Claude popup

`<space>ac` shows Claude; `<space>as` also types the screen's selected
context (`claude_context`) into Claude's prompt without submitting it.
`claude_popup.rs` keeps Claude in a detached tmux session named
`finlarp-claude` and shows it with `tmux display-popup -E` over the pane `fl`
runs in. Closing the popup (prefix-d) leaves Claude running, and the next
`<space>ac` shows the same conversation. This needs `fl` to run inside tmux;
otherwise the screen shows "claude: Claude popup needs fl run inside tmux".

## Adding a screen

1. `src/screens/<name>.rs` (or `<name>/mod.rs`) exposing
   `pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<impl Screen>`.
   A missing cache becomes an in-screen message, never a panic.
2. Compose `layout::render_frame`, `SectionList`, `BlockView`,
   `render_source_bar`, `SourceInspector` and `help`; one `const KEYS`;
   `source_action` as the fallthrough for ↵ / v / y.
3. Register in `screens/mod.rs`, and add the name to `SCREENS` and the
   `match` in `main.rs`. Add TestBackend tests.

## Adding a block type

1. Add a `model::Block` variant (serde `type` tag, lowercase); every item
   gets a `src: Option<Source>`.
2. Extend `Block::title` / `len` / `source`: all the cursor and audit need.
3. Render it in `ui/block_view.rs` (reuse `ui::charts`) and emit the same
   JSON shape from the Python producer (`py/derive/dossier.py`, `canslim.py`).

## Testing

- **Render tests** draw into a `TestBackend` buffer and assert on its text.
  Screens load JSON fixtures (`src/screens/fixtures/*.json`,
  `search/fixture.json`) via `include_str!`; chart builds synthetic history.
  Include tiny sizes: a render must never panic.
- **Event loop tests** (`app.rs`) drive `event_loop` with a scripted
  `Events` source: redraw skipping, resize, Ctrl-C, exit codes, key release.
- **Screen GIFs:** `just gifs` drives each screen in a named tmux session,
  captures the pane with colours and paints it to a GIF (`py/jobs/record_screens.py`).
  Add a `Spec` there when a screen is ready to show; leave out screens that show
  personal or mock data.
- **Visual check:** release binary in a detached tmux session:
  ```
  tmux new-session -d -s c5 -x 160 -y 40 'cargo run --release -- chart'
  tmux capture-pane -p -t c5      # -e keeps colours
  tmux send-keys -t c5 h
  ```
