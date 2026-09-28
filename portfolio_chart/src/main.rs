// Entry point for every security_spread TUI: one binary, one DuckDB file,
// several screens (src/screens/*). Launched by ui/portfolio_chart.lua in a
// tmux popup (or a floating nvim :terminal outside tmux).
//
// CLI: `portfolio_chart <bg> <fg_up> <fg_down> [screen] [arg]`
//   bg/fg_up/fg_down  #rrggbb from nvim's colorscheme; "" = terminal default
//   screen            chart (default) | canslim | dossier | search
//   arg               screen argument (symbol, query, ...)
// Env: SECURITY_SPREAD_DB overrides the DuckDB path;
//      SECURITY_SPREAD_ACTION_FILE receives an NvimAction on handoff (app.rs).

mod app;
mod db;
mod model;
mod screens;
mod ui;

use std::env;
use std::path::PathBuf;

use crate::ui::theme::Theme;

/// Parsed command line.
#[derive(Debug, PartialEq)]
struct Cli {
    bg: Option<String>,
    fg_up: Option<String>,
    fg_down: Option<String>,
    screen: String,
    arg: Option<String>,
}

const SCREENS: &[&str] = &["chart", "canslim", "dossier", "earnings", "search"];

/// Positional parse of everything after argv[0]. Empty strings are treated
/// as absent (Lua passes "" for "no explicit colour").
fn parse_args(args: &[String]) -> Result<Cli, String> {
    let get = |i: usize| args.get(i).filter(|s| !s.is_empty()).cloned();
    let screen = get(3).unwrap_or_else(|| "chart".to_string());
    if !SCREENS.contains(&screen.as_str()) {
        return Err(format!(
            "unknown screen {screen:?}\nusage: portfolio_chart <bg> <fg_up> <fg_down> [{}] [arg]",
            SCREENS.join("|")
        ));
    }
    Ok(Cli {
        bg: get(0),
        fg_up: get(1),
        fg_down: get(2),
        screen,
        arg: get(4),
    })
}

fn db_path() -> PathBuf {
    if let Some(p) = env::var_os("SECURITY_SPREAD_DB") {
        return PathBuf::from(p);
    }
    let home = env::var_os("HOME").map(PathBuf::from).unwrap_or_default();
    home.join(".local/share/nvim/security_spread.duckdb")
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let cli = match parse_args(&args) {
        Ok(c) => c,
        Err(msg) => {
            eprintln!("{msg}");
            std::process::exit(2);
        }
    };
    let ctx = app::Ctx {
        db_path: db_path(),
        theme: Theme::from_args(
            cli.bg.as_deref(),
            cli.fg_up.as_deref(),
            cli.fg_down.as_deref(),
        ),
    };
    let arg = cli.arg;
    let res = match cli.screen.as_str() {
        "canslim" => screens::canslim::open(&ctx, arg).and_then(|mut s| app::run(&mut s)),
        "dossier" => screens::dossier::open(&ctx, arg).and_then(|mut s| app::run(&mut s)),
        "earnings" => screens::earnings_report::open(&ctx, arg).and_then(|mut s| app::run(&mut s)),
        "search" => screens::search::open(&ctx, arg).and_then(|mut s| app::run(&mut s)),
        _ => screens::chart::open(&ctx, arg).and_then(|mut s| app::run(&mut s)),
    };
    match res {
        Ok(code) => std::process::exit(code),
        Err(e) => {
            eprintln!("portfolio_chart: {e}");
            // stderr dies with the popup/float; hand the message to nvim too
            if let Ok(path) = env::var(app::ACTION_FILE_ENV) {
                let _ = std::fs::write(
                    path,
                    serde_json::json!({ "error": e.to_string() }).to_string(),
                );
            }
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn args(v: &[&str]) -> Vec<String> {
        v.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn defaults_to_chart_with_no_colours() {
        let c = parse_args(&args(&[])).expect("parse");
        assert_eq!(
            c,
            Cli {
                bg: None,
                fg_up: None,
                fg_down: None,
                screen: "chart".into(),
                arg: None
            }
        );
        let c = parse_args(&args(&["", "", "", ""])).expect("parse");
        assert_eq!(c.screen, "chart");
    }

    #[test]
    fn full_positional() {
        let c =
            parse_args(&args(&["#101010", "#00ff00", "#ff0000", "canslim", "MU"])).expect("parse");
        assert_eq!(c.bg.as_deref(), Some("#101010"));
        assert_eq!(c.screen, "canslim");
        assert_eq!(c.arg.as_deref(), Some("MU"));
    }

    #[test]
    fn rejects_unknown_screen() {
        assert!(parse_args(&args(&["", "", "", "nope"])).is_err());
    }
}
