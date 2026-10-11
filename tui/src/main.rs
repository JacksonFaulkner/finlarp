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
// | universe | diagrams | events | chat. canslim/dossier without a ticker open a ticker picker.
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
    "chat",
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
[home|chart|portfolio|canslim|dossier|earnings|search|universe|diagrams|events|chat] [arg]";

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

/// Builds one screen (running the Python cache build first for canslim/dossier
/// when a ticker is given). No ticker opens a ticker picker.
fn build_screen(
    ctx: &app::Ctx,
    screen: &str,
    arg: Option<String>,
) -> std::io::Result<Box<dyn app::Screen>> {
    use screens::{
        canslim, chart, chat, diagrams, dossier, earnings_report, events, home, pick, portfolio,
        search, universe,
    };
    Ok(match (screen, upper(arg.clone())) {
        ("canslim", None) => Box::new(pick::open_symbols(ctx, "canslim")?),
        ("dossier", None) => Box::new(pick::open_symbols(ctx, "dossier")?),
        // Open from cache right away; the screen refreshes itself in the background.
        ("canslim", Some(sym)) => Box::new(canslim::open(ctx, Some(sym))?),
        ("dossier", Some(sym)) => Box::new(dossier::open(ctx, Some(sym))?),
        ("chat", _) => Box::new(chat::open(ctx, arg)?),
        ("home", _) => Box::new(home::open(ctx)?),
        ("portfolio", _) => Box::new(portfolio::open(ctx, arg)?),
        ("earnings", _) => Box::new(earnings_report::open(ctx, arg)?),
        ("search", _) => Box::new(search::open(ctx, arg)?),
        ("universe", _) => Box::new(universe::open(ctx, arg)?),
        ("events", _) => Box::new(events::open(ctx, arg)?),
        ("diagrams", _) => Box::new(diagrams::open(ctx, arg)?),
        _ => Box::new(chart::open(ctx, arg)?),
    })
}

/// `fl diagrams pdf [dir]`: exports and exits, no screen.
fn export_diagram_pdfs(ctx: &app::Ctx, arg: &str) -> std::io::Result<()> {
    let dir = Some(arg.trim())
        .filter(|d| !d.is_empty())
        .unwrap_or("diagrams-pdf");
    for p in screens::diagrams::export_pdfs(std::path::Path::new(dir), &ctx.theme)? {
        println!("{p}");
    }
    Ok(())
}

/// Runs a stack of live screens. A screen/picker request pushes the new screen
/// on top (a picker is replaced by what it picks, so back skips it); q/esc in
/// the top screen pops to the one beneath with its state intact. The session
/// ends when the bottom screen quits, or on a nonzero exit code.
fn run_session(ctx: &app::Ctx, start: &str, arg: Option<String>) -> std::io::Result<i32> {
    use app::NvimAction;
    if start == "diagrams" {
        if let Some(rest) = arg.as_deref().and_then(|a| a.strip_prefix("pdf")) {
            export_diagram_pdfs(ctx, rest)?;
            return Ok(0);
        }
    }
    // (screen, is_picker)
    let mut stack: Vec<(Box<dyn app::Screen>, bool)> = vec![(
        build_screen(ctx, start, arg.clone())?,
        upper(arg).is_none() && matches!(start, "canslim" | "dossier"),
    )];
    loop {
        let top = stack.last_mut().expect("stack never empty here");
        let exit = app::run(top.0.as_mut())?;
        let next = match exit.handoff {
            Some(NvimAction::Screen { screen, arg }) => Some((screen, arg)),
            Some(NvimAction::Picker { screen }) => Some((screen, None)),
            _ => None,
        };
        match next {
            Some((screen, arg)) => {
                let is_picker = upper(arg.clone()).is_none()
                    && matches!(screen.as_str(), "canslim" | "dossier");
                let child = build_screen(ctx, &screen, arg)?;
                if stack.last().is_some_and(|t| t.1) {
                    stack.pop(); // replace the picker with its pick
                }
                stack.push((child, is_picker));
            }
            None => {
                stack.pop();
                if exit.code != 0 || stack.is_empty() {
                    return Ok(exit.code);
                }
            }
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
