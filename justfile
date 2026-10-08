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
