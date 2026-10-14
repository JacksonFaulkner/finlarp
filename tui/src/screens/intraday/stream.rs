// Client for `py/sources/intraday_stream.py --serve`: one long-lived Python
// process that seeds each symbol's day over REST, then folds Yahoo websocket
// ticks into 1-minute bars. JSON lines both ways (see the script's docstring).
//
// A reader thread parses stdout into `Event`s on a channel the screen drains
// from `tick`; commands go the other way through `send`. Dropping the Stream
// closes the child's stdin (it exits when stdin ends) and kills it.

use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread;

use serde_json::Value;

use super::data::Bar1;

#[derive(Debug, Clone, PartialEq)]
pub enum Event {
    /// Whole day of 1m bars for a symbol (pre/post included).
    Seed {
        sym: String,
        prev_close: Option<f64>,
        /// Regular session open / close, epoch seconds.
        reg: Option<(i64, i64)>,
        bars: Vec<Bar1>,
    },
    /// The forming minute.
    Bar {
        sym: String,
        bar: Bar1,
    },
    Status {
        live: bool,
        msg: String,
    },
    Error {
        sym: String,
        msg: String,
    },
}

pub struct Stream {
    stdin: Option<ChildStdin>,
    child: Option<Child>,
    pub rx: Receiver<Event>,
    /// Every command written (kept for tests and debugging).
    pub sent: Vec<String>,
}

impl Stream {
    /// Spawn the feed. Never fails: spawn errors arrive as an `Event::Status`.
    pub fn spawn() -> Self {
        let (tx, rx) = mpsc::channel();
        let plugin = crate::pyrun::plugin_dir();
        let child = Command::new(crate::pyrun::python(&plugin))
            .arg(plugin.join("py/sources/intraday_stream.py"))
            .arg("--serve")
            .current_dir(&plugin)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn();
        match child {
            Ok(mut child) => {
                let stdin = child.stdin.take();
                if let Some(out) = child.stdout.take() {
                    thread::spawn(move || read_loop(out, tx));
                }
                Self {
                    stdin,
                    child: Some(child),
                    rx,
                    sent: Vec::new(),
                }
            }
            Err(e) => {
                let _ = tx.send(Event::Status {
                    live: false,
                    msg: format!("intraday_stream.py: {e}"),
                });
                Self {
                    stdin: None,
                    child: None,
                    rx,
                    sent: Vec::new(),
                }
            }
        }
    }

    /// A stream with no process behind it; feed it through the returned sender.
    #[cfg(test)]
    pub fn detached() -> (Self, Sender<Event>) {
        let (tx, rx) = mpsc::channel();
        (
            Self {
                stdin: None,
                child: None,
                rx,
                sent: Vec::new(),
            },
            tx,
        )
    }

    /// Replace the watched symbols.
    pub fn set_symbols(&mut self, symbols: &[String]) {
        let line = serde_json::json!({"cmd": "set", "symbols": symbols}).to_string();
        self.send(line);
    }

    /// Re-seed every symbol from REST (the feed also does this every minute).
    pub fn resync(&mut self, symbols: &[String]) {
        let _ = symbols;
        self.send(serde_json::json!({"cmd": "resync"}).to_string());
    }

    fn send(&mut self, line: String) {
        if let Some(stdin) = self.stdin.as_mut() {
            let _ = writeln!(stdin, "{line}").and_then(|_| stdin.flush());
        }
        self.sent.push(line);
    }
}

impl Drop for Stream {
    fn drop(&mut self) {
        self.stdin = None; // EOF: the script exits on its own
        if let Some(mut c) = self.child.take() {
            let _ = c.kill();
            let _ = c.wait();
        }
    }
}

fn read_loop(out: impl std::io::Read, tx: Sender<Event>) {
    for line in BufReader::new(out).lines() {
        let Ok(line) = line else { break };
        if let Some(ev) = parse_line(&line) {
            if tx.send(ev).is_err() {
                break;
            }
        }
    }
    let _ = tx.send(Event::Status {
        live: false,
        msg: "feed process ended".into(),
    });
}

fn bar_from(v: &Value) -> Option<Bar1> {
    let a = v.as_array()?;
    Some(Bar1 {
        t: a.first()?.as_i64()?,
        o: a.get(1)?.as_f64()?,
        h: a.get(2)?.as_f64()?,
        l: a.get(3)?.as_f64()?,
        c: a.get(4)?.as_f64()?,
        v: a.get(5)?.as_f64()?.max(0.0) as u64,
    })
}

pub fn parse_line(line: &str) -> Option<Event> {
    let v: Value = serde_json::from_str(line).ok()?;
    let sym = || v["sym"].as_str().map(str::to_string);
    match v["ev"].as_str()? {
        "seed" => {
            let reg = v["reg"]
                .as_array()
                .and_then(|r| Some((r.first()?.as_i64()?, r.get(1)?.as_i64()?)));
            Some(Event::Seed {
                sym: sym()?,
                prev_close: v["prev_close"].as_f64(),
                reg,
                bars: v["bars"].as_array()?.iter().filter_map(bar_from).collect(),
            })
        }
        "bar" => Some(Event::Bar {
            sym: sym()?,
            bar: bar_from(&v["bar"])?,
        }),
        "status" => Some(Event::Status {
            live: v["state"].as_str() == Some("live"),
            msg: v["msg"].as_str().unwrap_or("").to_string(),
        }),
        "error" => Some(Event::Error {
            sym: sym().unwrap_or_default(),
            msg: v["msg"].as_str().unwrap_or("").to_string(),
        }),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_seed_bar_and_status_lines() {
        let seed = r#"{"ev":"seed","sym":"WDC","prev_close":380.71,"reg":[1791984600,1792008000],"bars":[[1791994380,368.2,368.3,368.1,368.3,1200]]}"#;
        let Some(Event::Seed {
            sym,
            prev_close,
            reg,
            bars,
        }) = parse_line(seed)
        else {
            panic!("seed");
        };
        assert_eq!((sym.as_str(), prev_close), ("WDC", Some(380.71)));
        assert_eq!(reg, Some((1791984600, 1792008000)));
        assert_eq!(bars.len(), 1);
        assert_eq!(bars[0].v, 1200);

        let bar = parse_line(r#"{"ev":"bar","sym":"WDC","bar":[1791994440,1,2,0.5,1.5,7]}"#);
        assert_eq!(
            bar,
            Some(Event::Bar {
                sym: "WDC".into(),
                bar: Bar1 {
                    t: 1791994440,
                    o: 1.0,
                    h: 2.0,
                    l: 0.5,
                    c: 1.5,
                    v: 7
                }
            })
        );
        assert_eq!(
            parse_line(r#"{"ev":"status","state":"live","msg":"ok"}"#),
            Some(Event::Status {
                live: true,
                msg: "ok".into()
            })
        );
        assert_eq!(parse_line("garbage"), None);
        assert_eq!(parse_line(r#"{"ev":"bar","sym":"X","bar":[1,2]}"#), None);
    }

    #[test]
    fn set_symbols_writes_a_json_command() {
        let (mut s, _tx) = Stream::detached();
        s.set_symbols(&["MKSI".into(), "WDC".into()]);
        assert_eq!(
            s.sent,
            vec![r#"{"cmd":"set","symbols":["MKSI","WDC"]}"#.to_string()]
        );
    }
}
