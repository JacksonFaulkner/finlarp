# Dev tasks for finlarp.
# Run with `just <recipe>` (or `uvx --from rust-just just <recipe>`).

crate := "tui/Cargo.toml"

default: check

# one-time after a clone: python env (editable install) + the TUI binary
setup:
    uv sync
    cargo build --release --manifest-path {{crate}}
    uvx prek install

build:
    cargo build --release --manifest-path {{crate}}

# Claude Code in its own tmux window. Not a popup: closing a popup kills its
# process, which would end the session. Reuses the window if it already exists.
claude:
    #!/usr/bin/env sh
    set -eu
    if tmux list-windows -F '#{window_name}' | grep -qx claude; then
        tmux select-window -t claude
    else
        tmux new-window -n claude -c "{{justfile_directory()}}" claude
    fi

# put `fl` on PATH: symlink into ~/.local/bin so a rebuild updates it in place
install: build
    mkdir -p {{env("HOME")}}/.local/bin
    ln -sf {{justfile_directory()}}/tui/target/release/fl {{env("HOME")}}/.local/bin/fl

test:
    cargo test --release --manifest-path {{crate}}

# frame cost of every orbitable 3D diagram scene, slowest first (see tools/poly3d/CLAUDE.md)
# e.g. just bench-3d FL_BENCH_FILTER="TOP METAL" FL_BENCH_SIZE=2400x1320
bench-3d *env:
    env {{env}} cargo test --release --manifest-path {{crate}} bench_3d -- --ignored --nocapture

fmt:
    cargo fmt --manifest-path {{crate}}

lint:
    uv run ruff check .
    cargo fmt --check --manifest-path {{crate}}
    cargo clippy --release --manifest-path {{crate}} -- -D warnings

check: lint test

# git hooks from .pre-commit-config.yaml (prek is a fast pre-commit drop-in)
hooks:
    uvx prek install

# data refresh (py/jobs/refresh.py); add --dry-run to see the plan
refresh mode="daily" *args="":
    uv run --env-file .env python -m jobs.refresh {{mode}} {{args}}

# re-record docs/screens/*.gif from the release binary (needs tmux; pillow is fetched by uv, not a project dep)
gifs *args="":
    cd py && uv run --with pillow python -m jobs.record_screens {{args}}

# squeeze screen: crowded shorts + price/volume trigger (extra args: --top 40, --min-si-pct 15, TICKER ...)
squeeze *args="":
    uv run python -m jobs.squeeze_scan {{args}}

# launchd agents: daily 18:30 weekdays + intraday every 30 min in market hours
schedule:
    sh py/jobs/launchd/install.sh

unschedule:
    sh py/jobs/launchd/install.sh uninstall
