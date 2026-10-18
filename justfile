# Dev tasks for finlarp.
# Run with `just <recipe>` (or `uvx --from rust-just just <recipe>`).

crate := "tui/Cargo.toml"
# stylua + selene come from mason (:MasonInstall stylua selene)
mason := env("HOME") / ".local/share/nvim/mason/bin"

default: check

# one-time after a clone: python env (editable install) + the TUI binary
setup:
    uv sync
    cargo build --release --manifest-path {{crate}}
    uvx prek install

build:
    cargo build --release --manifest-path {{crate}}

# put `fl` on PATH: symlink into ~/.local/bin so a rebuild updates it in place
install: build
    mkdir -p {{env("HOME")}}/.local/bin
    ln -sf {{justfile_directory()}}/tui/target/release/fl {{env("HOME")}}/.local/bin/fl

test:
    cargo test --release --manifest-path {{crate}}

fmt:
    {{mason}}/stylua lua
    cargo fmt --manifest-path {{crate}}

lint:
    {{mason}}/selene lua
    {{mason}}/stylua --check lua
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
