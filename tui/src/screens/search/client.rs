// Talks to `py/derive/search.py --serve`: one long-lived Python process
// holding the DuckDB index + fts extension open (~100ms/query warm versus
// ~350ms for a process per keystroke, and the query parser stays in one
// place). JSON lines both ways, see the search.py module docstring.
//
// One worker thread owns the child's stdin/stdout and does strict
// request -> reply turns. Before each turn it drains the request channel and
// keeps only the newest query and newest `get`, so a burst of keystrokes
// costs one query, not a queue of stale ones. The UI thread never blocks:
// it sends on `tx` and polls `rx` from Screen::tick.

use std::collections::BTreeMap;
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, Receiver, Sender, TryRecvError};
use std::thread;

use serde::{Deserialize, Serialize};

/// One chunk, as search.py returns it (hits and `get` rows share the shape).
#[derive(Debug, Clone, Default, Deserialize, PartialEq)]
pub struct Hit {
    pub id: i64,
    #[serde(default)]
    pub ticker: String,
    #[serde(rename = "type", default)]
    pub kind: String,
    #[serde(default)]
    pub section: Option<String>,
    #[serde(default)]
    pub form: Option<String>,
    #[serde(default)]
    pub date: Option<String>,
    #[serde(default)]
    pub accn: Option<String>,
    #[serde(default)]
    pub seq: Option<i64>,
    #[serde(default)]
    pub text: String,
    #[serde(default)]
    pub score: Option<f64>,
    #[serde(default)]
    pub url: Option<String>,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
#[serde(untagged)]
pub enum Request {
    Query { id: u64, q: String, k: usize },
    Get { id: u64, get: i64, context: u32 },
}

impl Request {
    fn is_query(&self) -> bool {
        matches!(self, Request::Query { .. })
    }
}

/// Every reply field is optional: queries fill results/facets/terms, gets
/// fill rows, failures fill error.
#[derive(Debug, Clone, Default, Deserialize)]
pub struct Reply {
    #[serde(default)]
    pub id: Option<u64>,
    #[serde(default)]
    pub results: Vec<Hit>,
    /// dim -> [[value, count], ...], top N by count (year: newest first).
    #[serde(default)]
    pub facets: BTreeMap<String, Vec<(Option<String>, u64)>>,
    #[serde(default)]
    pub terms: Vec<String>,
    #[serde(default)]
    pub rows: Vec<Hit>,
    #[serde(default)]
    pub ms: Option<u64>,
    #[serde(default)]
    pub error: Option<String>,
}

/// Handle held by the screen. Dropping it closes the request channel, which
/// ends the worker, which kills the child.
pub struct Client {
    pub tx: Sender<Request>,
    pub rx: Receiver<Reply>,
}

impl Client {
    /// Spawn the server. Never fails: spawn errors arrive as an error Reply.
    pub fn spawn() -> Self {
        let (tx, req_rx) = mpsc::channel::<Request>();
        let (reply_tx, rx) = mpsc::channel::<Reply>();
        let plugin = crate::pyrun::plugin_dir();
        let child = Command::new(crate::pyrun::python(&plugin))
            .arg(plugin.join("py/derive/search.py"))
            .arg("--serve")
            .current_dir(&plugin)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn();
        match child {
            Ok(child) => {
                thread::spawn(move || worker(child, req_rx, reply_tx));
            }
            Err(e) => {
                let _ = reply_tx.send(Reply {
                    error: Some(format!("search.py --serve: {e}")),
                    ..Reply::default()
                });
            }
        }
        Self { tx, rx }
    }
}

fn worker(mut child: Child, req_rx: Receiver<Request>, reply_tx: Sender<Reply>) {
    let (Some(mut stdin), Some(stdout)) = (child.stdin.take(), child.stdout.take()) else {
        let _ = reply_tx.send(Reply {
            error: Some("search.py: no pipes".into()),
            ..Reply::default()
        });
        let _ = child.kill();
        return;
    };
    let mut stdout = BufReader::new(stdout);
    let mut pending: Vec<Request> = Vec::new();
    'outer: loop {
        if pending.is_empty() {
            match req_rx.recv() {
                Ok(r) => pending.push(r),
                Err(_) => break, // screen gone
            }
        }
        // coalesce: newest query + newest get, query first
        loop {
            match req_rx.try_recv() {
                Ok(r) => pending.push(r),
                Err(TryRecvError::Empty) => break,
                Err(TryRecvError::Disconnected) => break 'outer,
            }
        }
        let q = pending
            .iter()
            .rposition(Request::is_query)
            .map(|i| pending[i].clone());
        let g = pending
            .iter()
            .rposition(|r| !r.is_query())
            .map(|i| pending[i].clone());
        pending.clear();
        for req in q.into_iter().chain(g) {
            let reply = turn(&mut stdin, &mut stdout, &req);
            let dead = reply.is_err();
            let reply = reply.unwrap_or_else(|e| Reply {
                error: Some(e),
                ..Reply::default()
            });
            if reply_tx.send(reply).is_err() || dead {
                break 'outer;
            }
        }
    }
    let _ = child.kill();
    let _ = child.wait();
}

/// One request/reply exchange. Err = the server is unusable.
fn turn(stdin: &mut impl Write, stdout: &mut impl BufRead, req: &Request) -> Result<Reply, String> {
    let line = serde_json::to_string(req).map_err(|e| e.to_string())?;
    writeln!(stdin, "{line}")
        .and_then(|_| stdin.flush())
        .map_err(|e| format!("search.py exited: {e}"))?;
    let mut buf = String::new();
    match stdout.read_line(&mut buf) {
        Ok(0) => Err("search.py exited (index missing? run `search.py build`)".into()),
        Ok(_) => Ok(serde_json::from_str(&buf).unwrap_or_else(|e| Reply {
            error: Some(format!("bad reply: {e}")),
            ..Reply::default()
        })),
        Err(e) => Err(format!("search.py read: {e}")),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn request_wire_format() {
        let q = serde_json::to_string(&Request::Query {
            id: 3,
            q: "t:MRVL".into(),
            k: 50,
        })
        .unwrap_or_default();
        assert_eq!(q, r#"{"id":3,"q":"t:MRVL","k":50}"#);
        let g = serde_json::to_string(&Request::Get {
            id: 4,
            get: 12,
            context: 1,
        })
        .unwrap_or_default();
        assert_eq!(g, r#"{"id":4,"get":12,"context":1}"#);
    }

    #[test]
    fn turn_reads_one_reply() {
        let mut out = Vec::new();
        let mut inp = std::io::Cursor::new(
            b"{\"id\":1,\"results\":[],\"facets\":{\"ticker\":[[\"MRVL\",3]]}}\n".to_vec(),
        );
        let r = turn(
            &mut out,
            &mut inp,
            &Request::Query {
                id: 1,
                q: "x".into(),
                k: 5,
            },
        );
        let r = r.unwrap_or_default();
        assert_eq!(r.id, Some(1));
        assert_eq!(r.facets["ticker"], vec![(Some("MRVL".to_string()), 3)]);
        // EOF = dead server
        assert!(
            turn(
                &mut out,
                &mut inp,
                &Request::Query {
                    id: 2,
                    q: "x".into(),
                    k: 5
                }
            )
            .is_err()
        );
    }
}
