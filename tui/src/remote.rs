// Moves the screen the user is looking at, from outside the process.
//
//   finlarp MCP show_screen ──unix socket──▶ running fl ──Action::Route──▶ the screen pushes
//
// Each running `fl` listens on <temp dir>/fl-control-<pid>.sock. A client writes one JSON
// line and gets one JSON line back ({"ok": true, ...} or {"ok": false, "error": ...}):
//   {"screen": "diagrams", "arg": "memory"}   push a screen (q/esc returns to the one open)
//   {"tool": "open_node", "args": {...}}       a tool call on the open screen, in place
//                                              (Diagrams answers the diagrams_ipc tools)

use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::PathBuf;
use std::sync::mpsc::{Receiver, Sender, TryRecvError, channel};
use std::sync::{Mutex, OnceLock};
use std::time::Duration;

use serde_json::{Value, json};

use crate::app::Route;

/// A request waiting for the event loop.
pub enum Remote {
    /// Push this screen.
    Route(Route),
    /// Run a tool on the open screen; its result goes back on `reply`.
    Tool { tool: String, args: Value, reply: Sender<Value> },
}

static INBOX: OnceLock<Mutex<Receiver<Remote>>> = OnceLock::new();

/// How long a tool call may wait for the screen to answer.
const REPLY_TIMEOUT: Duration = Duration::from_secs(30);

/// This process's socket. Clients pick the newest one that answers.
pub fn socket_path() -> PathBuf {
    std::env::temp_dir().join(format!("fl-control-{}.sock", std::process::id()))
}

/// Starts listening for this process. Call once, in the interactive session only.
pub fn start(screens: &[&str]) -> std::io::Result<()> {
    let path = socket_path();
    let _ = std::fs::remove_file(&path);
    let listener = UnixListener::bind(&path)?;
    let (tx, rx) = channel::<Remote>();
    let screens: Vec<String> = screens.iter().map(|s| s.to_string()).collect();
    std::thread::spawn(move || {
        for conn in listener.incoming().map_while(Result::ok) {
            let (tx, screens) = (tx.clone(), screens.clone());
            std::thread::spawn(move || serve(conn, &tx, &screens));
        }
    });
    let _ = INBOX.set(Mutex::new(rx));
    Ok(())
}

/// Removes this process's socket file. Call when the session ends.
pub fn stop() {
    let _ = std::fs::remove_file(socket_path());
}

/// The next request from a client, if one is waiting. The event loop calls this each pass.
pub fn next() -> Option<Remote> {
    let rx = INBOX.get()?.lock().ok()?;
    match rx.try_recv() {
        Ok(route) => Some(route),
        Err(TryRecvError::Empty | TryRecvError::Disconnected) => None,
    }
}

/// One connection: a request per line in, its result per line out.
fn serve(conn: UnixStream, tx: &Sender<Remote>, screens: &[String]) {
    let Ok(mut out) = conn.try_clone() else {
        return;
    };
    let closing = || json!({ "ok": false, "error": "fl is closing" });
    for line in BufReader::new(conn).lines().map_while(Result::ok) {
        let reply = match parse(&line, screens) {
            Ok(Parsed::Route(route)) => match tx.send(Remote::Route(route)) {
                Ok(()) => json!({ "ok": true }),
                Err(_) => closing(),
            },
            Ok(Parsed::Tool(tool, args)) => {
                let (reply, got) = channel();
                match tx.send(Remote::Tool { tool, args, reply }) {
                    Ok(()) => got.recv_timeout(REPLY_TIMEOUT).unwrap_or_else(|_| {
                        json!({ "ok": false, "error": "the screen did not answer in time" })
                    }),
                    Err(_) => closing(),
                }
            }
            Err(e) => json!({ "ok": false, "error": e }),
        };
        if writeln!(out, "{reply}").is_err() {
            return;
        }
    }
}

#[derive(Debug, PartialEq)]
enum Parsed {
    Route(Route),
    Tool(String, Value),
}

/// A request line as what it asks for. Unknown screens are refused with the valid names.
fn parse(line: &str, screens: &[String]) -> Result<Parsed, String> {
    let v: Value = serde_json::from_str(line).map_err(|e| format!("bad request: {e}"))?;
    if let Some(tool) = v["tool"].as_str().filter(|t| !t.is_empty()) {
        let args = if v["args"].is_object() { v["args"].clone() } else { json!({}) };
        return Ok(Parsed::Tool(tool.to_string(), args));
    }
    let screen = v["screen"].as_str().unwrap_or("").to_string();
    if !screens.contains(&screen) {
        return Err(format!("unknown screen {screen:?}. valid: {}", screens.join(" ")));
    }
    let arg = v["arg"].as_str().map(str::trim).filter(|a| !a.is_empty()).map(str::to_string);
    Ok(Parsed::Route(Route::Screen { screen, arg }))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn screens() -> Vec<String> {
        ["home", "diagrams", "memory"].iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn parses_screen_and_arg() {
        assert_eq!(
            parse(r#"{"screen":"diagrams","arg":"memory"}"#, &screens()),
            Ok(Parsed::Route(Route::Screen { screen: "diagrams".into(), arg: Some("memory".into()) }))
        );
    }

    #[test]
    fn empty_arg_is_none() {
        assert_eq!(
            parse(r#"{"screen":"home","arg":"  "}"#, &screens()),
            Ok(Parsed::Route(Route::Screen { screen: "home".into(), arg: None }))
        );
    }

    #[test]
    fn unknown_screen_is_refused_with_valid_names() {
        let e = parse(r#"{"screen":"nope"}"#, &screens()).unwrap_err();
        assert!(e.contains("unknown screen") && e.contains("diagrams"), "{e}");
    }

    #[test]
    fn tool_call_parses_with_args() {
        assert_eq!(
            parse(r#"{"tool":"open_node","args":{"node":"HBM STACK"}}"#, &screens()),
            Ok(Parsed::Tool("open_node".into(), json!({"node": "HBM STACK"})))
        );
    }

    #[test]
    fn bad_json_is_refused() {
        assert!(parse("not json", &screens()).unwrap_err().starts_with("bad request"));
    }
}
