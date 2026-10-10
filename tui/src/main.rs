// Entry point for every finlarp TUI: one binary (`fl`), one DuckDB file,
// several screens (src/screens/*).
//
//   fl                    home menu (same as `fl .`)
//   fl <screen> [arg]     open a screen directly: fl dossier NVDA
//   flags                 --bg/--up/--down #rrggbb: colours from nvim's
//                         colorscheme (ui/tui.lua passes them); omitted =
//                         terminal default background
//
// Screens: home | chart | portfolio | canslim | dossier | earnings | search
// | universe | diagrams | events. canslim/dossier without a ticker open a ticker picker.
//
// Launched by ui/tui.lua in a tmux popup (or a floating nvim :terminal), or
// by hand. Inside nvim a screen that wants another screen hands the request
// back through $FINLARP_ACTION_FILE; standalone, `run_session` below opens it
// in-process and returns to home when a screen quits (if you started there).
// Env: FINLARP_DB overrides the DuckDB path.

mod app;
mod db;
mod model;
mod pyrun;
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

const SCREENS: &[&str] = &[
    "home",
    "chart",
    "portfolio",
    "canslim",
    "dossier",
    "earnings",
    "search",
    "universe",
    "diagrams",
    "events",
];

/// `[--bg C] [--up C] [--down C] [screen [arg...]]`. No screen or `.` is
/// home; empty colour values are treated as absent (Lua passes "" for "no
/// explicit colour"); the rest of the line is the screen argument, so
/// `fl search t:MRVL guidance` works unquoted.
fn parse_args(args: &[String]) -> Result<Cli, String> {
    let mut cli = Cli {
        bg: None,
        fg_up: None,
        fg_down: None,
        screen: "home".to_string(),
        arg: None,
    };
    let mut rest: Vec<&str> = Vec::new();
    let mut it = args.iter();
    while let Some(a) = it.next() {
        let (flag, inline) = match a.split_once('=') {
            Some((f, v)) if f.starts_with("--") => (f, Some(v.to_string())),
            _ => (a.as_str(), None),
        };
        let slot = match flag {
            "--bg" => &mut cli.bg,
            "--up" => &mut cli.fg_up,
            "--down" => &mut cli.fg_down,
            _ if rest.is_empty() && flag.starts_with("--") => {
                return Err(format!("unknown flag {flag}\n{USAGE}"));
            }
            _ => {
                rest.push(a);
                continue;
            }
        };
        let v = match inline {
            Some(v) => v,
            None => it.next().cloned().ok_or(format!("{flag} needs a value"))?,
        };
        *slot = Some(v).filter(|v| !v.is_empty());
    }
    if let Some((screen, arg)) = rest.split_first() {
        cli.screen = if *screen == "." { "home" } else { screen }.to_string();
        if !SCREENS.contains(&cli.screen.as_str()) {
            return Err(format!("unknown screen {screen:?}\n{USAGE}"));
        }
        let arg = arg.join(" ");
        cli.arg = Some(arg).filter(|a| !a.trim().is_empty());
    }
    Ok(cli)
}

const USAGE: &str = "usage: fl [--bg #rrggbb] [--up #rrggbb] [--down #rrggbb] \
[home|chart|portfolio|canslim|dossier|earnings|search|universe|diagrams|events] [arg]";

fn db_path() -> PathBuf {
    if let Some(p) = env::var_os("FINLARP_DB") {
        return PathBuf::from(p);
    }
    let home = env::var_os("HOME").map(PathBuf::from).unwrap_or_default();
    home.join(".local/share/nvim/finlarp.duckdb")
}

fn upper(arg: Option<String>) -> Option<String> {
    arg.map(|a| a.trim().to_uppercase())
        .filter(|a| !a.is_empty())
}

/// Opens one screen and runs it to completion. canslim/dossier build their
/// cache first (the Python side), and open a ticker picker when no ticker
/// was given.
fn run_screen(ctx: &app::Ctx, screen: &str, arg: Option<String>) -> std::io::Result<app::Exit> {
    use screens::{
        canslim, chart, diagrams, dossier, earnings_report, events, home, pick, portfolio, search,
        universe,
    };
    match (screen, upper(arg.clone())) {
        ("canslim", None) => app::run(&mut pick::open_symbols(ctx, "canslim")?),
        ("dossier", None) => app::run(&mut pick::open_symbols(ctx, "dossier")?),
        ("canslim", Some(sym)) => {
            eprintln!("fetching {sym} canslim...");
            if let Err(e) = pyrun::run_script("py/derive/canslim.py", &[&sym, "--force"]) {
                eprintln!("finlarp: {e}"); // open anyway: the screen shows what is cached
            }
            app::run(&mut canslim::open(ctx, Some(sym))?)
        }
        ("dossier", Some(sym)) => {
            eprintln!("building {sym} dossier...");
            if let Err(e) = pyrun::run_script("py/derive/dossier.py", &[&sym, "--if-stale", "12"]) {
                eprintln!("finlarp: {e}");
            }
            app::run(&mut dossier::open(ctx, Some(sym))?)
        }
        ("home", _) => app::run(&mut home::open(ctx)?),
        ("portfolio", _) => app::run(&mut portfolio::open(ctx, arg)?),
        ("earnings", _) => app::run(&mut earnings_report::open(ctx, arg)?),
        ("search", _) => app::run(&mut search::open(ctx, arg)?),
        ("universe", _) => app::run(&mut universe::open(ctx, arg)?),
        ("events", _) => app::run(&mut events::open(ctx, arg)?),
        ("diagrams", _) => match arg.as_deref().and_then(|a| a.strip_prefix("pdf")) {
            Some(dir) => {
                let dir = Some(dir.trim())
                    .filter(|d| !d.is_empty())
                    .unwrap_or("diagrams-pdf");
                for p in diagrams::export_pdfs(std::path::Path::new(dir), &ctx.theme)? {
                    println!("{p}");
                }
                Ok(app::Exit {
                    code: 0,
                    handoff: None,
                })
            }
            None => app::run(&mut diagrams::open(ctx, arg)?),
        },
        _ => app::run(&mut chart::open(ctx, arg)?),
    }
}

/// Runs screens until one ends the session. Inside nvim a handoff is written
/// to the action file by `app::run`, so this loop runs once. Standalone it
/// follows screen/picker requests, and falls back to home when a screen
/// quits if the session started at home.
fn run_session(ctx: &app::Ctx, start: &str, arg: Option<String>) -> std::io::Result<i32> {
    use app::NvimAction;
    let via_home = start == "home";
    let (mut screen, mut arg) = (start.to_string(), arg);
    loop {
        let exit = run_screen(ctx, &screen, arg.take())?;
        match exit.handoff {
            Some(NvimAction::Screen { screen: s, arg: a }) => (screen, arg) = (s, a),
            Some(NvimAction::Picker { screen: s }) => (screen, arg) = (s, None),
            _ if exit.code != 0 || !via_home || screen == "home" => return Ok(exit.code),
            _ => (screen, arg) = ("home".to_string(), None),
        }
    }
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
    match run_session(&ctx, &cli.screen, cli.arg) {
        Ok(code) => std::process::exit(code),
        Err(e) => {
            eprintln!("finlarp: {e}");
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

    fn cli(v: &[&str]) -> Cli {
        parse_args(&args(v)).expect("parse")
    }

    #[test]
    fn no_args_and_dot_open_home() {
        for v in [&[][..], &["."][..], &["home"][..]] {
            let c = cli(v);
            assert_eq!(c.screen, "home");
            assert_eq!(c.arg, None);
            assert_eq!((c.bg, c.fg_up, c.fg_down), (None, None, None));
        }
    }

    #[test]
    fn flags_screen_and_multiword_arg() {
        let c = cli(&[
            "--bg",
            "#101010",
            "--up=#00ff00",
            "--down",
            "",
            "search",
            "t:MRVL",
            "guidance",
        ]);
        assert_eq!(c.bg.as_deref(), Some("#101010"));
        assert_eq!(c.fg_up.as_deref(), Some("#00ff00"));
        assert_eq!(c.fg_down, None); // empty = absent
        assert_eq!(c.screen, "search");
        assert_eq!(c.arg.as_deref(), Some("t:MRVL guidance"));
    }

    #[test]
    fn symbol_arg() {
        let c = cli(&["canslim", "MU"]);
        assert_eq!(
            (c.screen.as_str(), c.arg.as_deref()),
            ("canslim", Some("MU"))
        );
    }

    #[test]
    fn rejects_unknown_screen_flag_and_missing_value() {
        assert!(parse_args(&args(&["nope"])).is_err());
        assert!(parse_args(&args(&["--wat", "x"])).is_err());
        assert!(parse_args(&args(&["--bg"])).is_err());
    }
}
