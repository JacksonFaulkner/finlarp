// How Claude's tool calls reach the diagram that is open.
//
//   claude -p ──stdio──▶ `fl diagram-mcp` ──unix socket──▶ the running fl (Diagrams)
//
// The running screen owns the socket (`Server`): a thread accepts connections and
// hands each request to the screen's tick over a channel, with a channel back for the
// result. A result can come late (a `wait`, a question the user has to answer), so the
// connection simply blocks until the screen replies.
//
// `fl diagram-mcp` is the other end: a small MCP server over stdio (JSON-RPC, one
// message per line) that lists the tools in `TOOLS` and forwards each call to the
// socket named by FL_DIAGRAM_SOCK. The screen validates every call and answers
// `{"ok":false,"error":...}` with the valid choices when it cannot run one, so a
// wrong name comes back to Claude as something it can fix.

use std::io::{self, BufRead, BufReader, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::PathBuf;
use std::sync::mpsc::{Receiver, Sender, channel};
use std::time::Duration;

use serde_json::{Value, json};

/// Env var that tells `fl diagram-mcp` which socket the open diagram listens on.
pub const SOCK_ENV: &str = "FL_DIAGRAM_SOCK";

/// How long a call may wait for the screen: a quiz waits on the user.
const REPLY_TIMEOUT: Duration = Duration::from_secs(600);

/// One tool call on its way to the screen.
pub struct Request {
    pub tool: String,
    pub args: Value,
    pub reply: Sender<Value>,
}

/// The screen's end: the socket and the calls that have arrived on it.
pub struct Server {
    pub path: PathBuf,
    pub rx: Receiver<Request>,
}

impl Server {
    pub fn start() -> io::Result<Server> {
        let path = std::env::temp_dir().join(format!("fl-diagram-{}.sock", std::process::id()));
        let _ = std::fs::remove_file(&path);
        let listener = UnixListener::bind(&path)?;
        let (tx, rx) = channel::<Request>();
        std::thread::spawn(move || {
            for conn in listener.incoming() {
                let Ok(conn) = conn else {
                    break;
                };
                let tx = tx.clone();
                std::thread::spawn(move || serve(conn, tx));
            }
        });
        Ok(Server { path, rx })
    }
}

impl Drop for Server {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.path);
    }
}

/// One connection: a request per line in, its result per line out.
fn serve(conn: UnixStream, tx: Sender<Request>) {
    let Ok(mut out) = conn.try_clone() else {
        return;
    };
    for line in BufReader::new(conn).lines().map_while(Result::ok) {
        let result = match serde_json::from_str::<Value>(&line) {
            Ok(v) => {
                let (reply, got) = channel();
                let req = Request {
                    tool: v["tool"].as_str().unwrap_or("").to_string(),
                    args: v["args"].clone(),
                    reply,
                };
                if tx.send(req).is_err() {
                    return;
                }
                got.recv_timeout(REPLY_TIMEOUT)
                    .unwrap_or_else(|_| fail("the diagram did not answer in time"))
            }
            Err(e) => fail(&format!("bad request: {e}")),
        };
        if writeln!(out, "{result}").is_err() {
            return;
        }
    }
}

pub fn fail(msg: &str) -> Value {
    json!({ "ok": false, "error": msg })
}

/// A tool as MCP lists it.
struct Tool {
    name: &'static str,
    about: &'static str,
    /// JSON Schema of the arguments.
    schema: fn() -> Value,
}

fn obj(props: Value, required: &[&str]) -> Value {
    json!({ "type": "object", "properties": props, "required": required, "additionalProperties": false })
}

fn no_args() -> Value {
    obj(json!({}), &[])
}

const VIEW_ABOUT: &str =
    "A view of the open node: \"overview\", a zoom-in letter (\"a\"), or a section number (\"3\").";

/// The steps a `sequence` may hold: every tool that changes the picture, as
/// {"do": <tool name>, ...that tool's arguments}.
pub const STEP_TOOLS: &[&str] = &[
    "open_node",
    "goto",
    "beat",
    "play",
    "pause",
    "camera",
    "note",
    "remove_note",
    "clear",
    "point",
    "caption",
    "labels",
    "wait",
];

const TOOLS: &[Tool] = &[
    Tool {
        name: "state",
        about: "What the user is looking at right now: tab, node, view, beat (with its caption and notes), the part names on the picture, the zoom-ins and sections of the node, and the notes that are up. Read-only.",
        schema: no_args,
    },
    Tool {
        name: "parts",
        about: "The part names each view of the open node labels, beat by beat: exactly the names `note.on`, `point.parts` and `ask_part` accept. Call it before pinning notes in a view you have not seen. Read-only.",
        schema: || {
            obj(
                json!({ "view": { "type": "string", "description": format!("{VIEW_ABOUT} Leave out for the overview and every zoom-in.") } }),
                &[],
            )
        },
    },
    Tool {
        name: "list_nodes",
        about: "Every tab and its nodes, each with a one-line description. Read-only.",
        schema: no_args,
    },
    Tool {
        name: "read_section",
        about: "The text of one numbered section of the open node's write-up. Read-only.",
        schema: || obj(json!({ "n": { "type": "integer", "minimum": 1 } }), &["n"]),
    },
    Tool {
        name: "open_node",
        about: "Open another node, on any tab, by its name (LITHO, HBM STACK). Lands on that node's overview. Returns the new state.",
        schema: || obj(json!({ "node": { "type": "string" } }), &["node"]),
    },
    Tool {
        name: "goto",
        about: "Move inside the open node. Give exactly one of: zoom (a zoom-in's letter), section (a write-up section's number), overview: true, menu: true. Returns the new state, with the part names now on the picture.",
        schema: || {
            obj(
                json!({
                    "zoom": { "type": "string", "minLength": 1, "maxLength": 1 },
                    "section": { "type": "integer", "minimum": 1 },
                    "overview": { "type": "boolean" },
                    "menu": { "type": "boolean" },
                }),
                &[],
            )
        },
    },
    Tool {
        name: "beat",
        about: "Jump to beat n (1-based) of the open animation and hold it there. Returns the beat's caption, notes and part names.",
        schema: || obj(json!({ "n": { "type": "integer", "minimum": 1 } }), &["n"]),
    },
    Tool {
        name: "play",
        about: "Let the open animation run.",
        schema: no_args,
    },
    Tool {
        name: "pause",
        about: "Hold the open animation where it is.",
        schema: no_args,
    },
    Tool {
        name: "camera",
        about: "Turn or zoom the 3D picture. yaw and pitch are degrees added to the current angle (yaw 90 = a quarter turn); zoom is a factor (1.5 = closer); reset: true returns to the default view. Only views with a 3D model turn.",
        schema: || {
            obj(
                json!({
                    "yaw": { "type": "number", "minimum": -360, "maximum": 360 },
                    "pitch": { "type": "number", "minimum": -90, "maximum": 90 },
                    "zoom": { "type": "number", "minimum": 0.3, "maximum": 4 },
                    "reset": { "type": "boolean" },
                }),
                &[],
            )
        },
    },
    Tool {
        name: "note",
        about: "Put a text box on the picture, or replace the one with the same id. `on` pins it to a part by the name the picture labels it with (see `parts`); without `on` it is a free box. Fails, listing the parts of the view, if `on` matches none. At most 4 notes up at once.",
        schema: || {
            obj(
                json!({
                    "id": { "type": "string", "maxLength": 16 },
                    "on": { "type": "string" },
                    "title": { "type": "string", "maxLength": 24 },
                    "text": { "type": "string", "minLength": 1, "maxLength": 160 },
                }),
                &["id", "text"],
            )
        },
    },
    Tool {
        name: "remove_note",
        about: "Take one note off the picture by its id.",
        schema: || obj(json!({ "id": { "type": "string" } }), &["id"]),
    },
    Tool {
        name: "clear",
        about: "Take everything you added off the picture: notes, rings and the caption.",
        schema: no_args,
    },
    Tool {
        name: "point",
        about: "Ring parts on the picture to say \"look here\" without text. Replaces the rings that are up; an empty list removes them. Names as in `parts`.",
        schema: || {
            obj(
                json!({ "parts": { "type": "array", "items": { "type": "string" }, "maxItems": 4 } }),
                &["parts"],
            )
        },
    },
    Tool {
        name: "caption",
        about: "Set the one line of text under the picture (empty removes it). For a sentence that belongs to the whole picture rather than one part.",
        schema: || {
            obj(
                json!({ "text": { "type": "string", "maxLength": 200 } }),
                &["text"],
            )
        },
    },
    Tool {
        name: "labels",
        about: "Show or hide the picture's own part names. Hide them before asking the user to name or find a part; show them again after.",
        schema: || obj(json!({ "show": { "type": "boolean" } }), &["show"]),
    },
    Tool {
        name: "wait",
        about: "Do nothing for ms milliseconds (at most 10000), so the user can read or watch before the next step.",
        schema: || {
            obj(
                json!({ "ms": { "type": "integer", "minimum": 100, "maximum": 10000 } }),
                &["ms"],
            )
        },
    },
    Tool {
        name: "sequence",
        about: "Play a whole walk-through in one call: an ordered list of steps, each {\"do\": <tool>, ...its arguments} where the tool is one of open_node, goto, beat, play, pause, camera, note, remove_note, clear, point, caption, labels, wait. Every step is checked first (note pins against the parts of the view the walk-through will be in by then); if any is wrong nothing runs and the error says which step and what is valid. Then the steps play on the user's screen, waits included, and the call returns when the last has run. Prefer this to many single calls.",
        schema: || {
            obj(
                json!({
                    "steps": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 40,
                        "items": {
                            "type": "object",
                            "properties": { "do": { "type": "string", "enum": STEP_TOOLS } },
                            "required": ["do"],
                        },
                    }
                }),
                &["steps"],
            )
        },
    },
    Tool {
        name: "ask",
        about: "Ask the user a multiple-choice question under the picture and wait for the answer. 2 to 4 choices; the user presses a, b, c or d. Returns the choice picked (or that the user skipped). Use it to have the user predict what happens next before you play it, or to check understanding. Say afterwards whether they were right and why.",
        schema: || {
            obj(
                json!({
                    "question": { "type": "string", "minLength": 1, "maxLength": 160 },
                    "choices": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 4,
                        "items": { "type": "string", "maxLength": 80 },
                    },
                }),
                &["question", "choices"],
            )
        },
    },
    Tool {
        name: "ask_part",
        about: "Ask the user to pick a part on the picture and wait: they move a ring from part to part and press enter. Returns the name of the part picked. Works in a view with a picture; hide the labels first (`labels`) to make it a recall exercise.",
        schema: || {
            obj(
                json!({ "question": { "type": "string", "minLength": 1, "maxLength": 160 } }),
                &["question"],
            )
        },
    },
];

pub fn tool_names() -> Vec<&'static str> {
    TOOLS.iter().map(|t| t.name).collect()
}

fn tools_list() -> Value {
    let list: Vec<Value> = TOOLS
        .iter()
        .map(|t| json!({ "name": t.name, "description": t.about, "inputSchema": (t.schema)() }))
        .collect();
    json!({ "tools": list })
}

/// Sends one call to the screen and waits for its result.
fn forward(
    conn: &mut Option<(UnixStream, BufReader<UnixStream>)>,
    tool: &str,
    args: &Value,
) -> Value {
    if conn.is_none() {
        let Some(path) = std::env::var_os(SOCK_ENV) else {
            return fail("no diagram is open (FL_DIAGRAM_SOCK is not set)");
        };
        match UnixStream::connect(&path).and_then(|s| Ok((s.try_clone()?, BufReader::new(s)))) {
            Ok(c) => *conn = Some(c),
            Err(e) => return fail(&format!("can't reach the diagram: {e}")),
        }
    }
    let Some((out, back)) = conn.as_mut() else {
        return fail("can't reach the diagram");
    };
    let req = json!({ "tool": tool, "args": args });
    let mut line = String::new();
    if writeln!(out, "{req}").is_err() || back.read_line(&mut line).unwrap_or(0) == 0 {
        *conn = None;
        return fail("the diagram closed");
    }
    serde_json::from_str(&line).unwrap_or_else(|_| fail("the diagram sent a bad result"))
}

/// One JSON-RPC message in, its response out (None for a notification).
fn handle(msg: &Value, conn: &mut Option<(UnixStream, BufReader<UnixStream>)>) -> Option<Value> {
    let id = msg.get("id").cloned()?;
    let result = match msg["method"].as_str().unwrap_or("") {
        "initialize" => json!({
            "protocolVersion": msg["params"]["protocolVersion"].as_str().unwrap_or("2024-11-05"),
            "capabilities": { "tools": {} },
            "serverInfo": { "name": "diagram", "version": env!("CARGO_PKG_VERSION") },
        }),
        "ping" => json!({}),
        "tools/list" => tools_list(),
        "tools/call" => {
            let name = msg["params"]["name"].as_str().unwrap_or("");
            let args = msg["params"].get("arguments").cloned().unwrap_or(json!({}));
            let out = if TOOLS.iter().any(|t| t.name == name) {
                forward(conn, name, &args)
            } else {
                fail(&format!(
                    "no tool {name:?}; tools: {}",
                    tool_names().join(", ")
                ))
            };
            let bad = out["ok"] == false;
            json!({
                "content": [{ "type": "text", "text": serde_json::to_string_pretty(&out).unwrap_or_default() }],
                "isError": bad,
            })
        }
        other => {
            return Some(json!({
                "jsonrpc": "2.0",
                "id": id,
                "error": { "code": -32601, "message": format!("method not found: {other}") },
            }));
        }
    };
    Some(json!({ "jsonrpc": "2.0", "id": id, "result": result }))
}

/// `fl diagram-mcp`: serve MCP on stdio until stdin closes.
pub fn run_mcp() -> i32 {
    let stdin = io::stdin();
    let mut stdout = io::stdout();
    let mut conn = None;
    for line in stdin.lock().lines().map_while(Result::ok) {
        let Ok(msg) = serde_json::from_str::<Value>(&line) else {
            continue;
        };
        if let Some(resp) = handle(&msg, &mut conn) {
            if writeln!(stdout, "{resp}").is_err() || stdout.flush().is_err() {
                return 1;
            }
        }
    }
    0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lists_tools_with_object_schemas_and_every_step_tool_exists() {
        let list = tools_list();
        let tools = list["tools"].as_array().unwrap();
        assert!(tools.len() >= 18, "{}", tools.len());
        for t in tools {
            assert_eq!(t["inputSchema"]["type"], "object", "{t}");
            assert!(t["description"].as_str().unwrap().len() > 20);
        }
        for step in STEP_TOOLS {
            assert!(tool_names().contains(step), "{step}");
        }
    }

    #[test]
    fn answers_the_mcp_handshake_and_ignores_notifications() {
        let mut conn = None;
        let init = handle(
            &json!({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}),
            &mut conn,
        )
        .unwrap();
        assert_eq!(init["result"]["protocolVersion"], "2025-06-18");
        assert!(init["result"]["capabilities"]["tools"].is_object());
        assert!(
            handle(
                &json!({"jsonrpc":"2.0","method":"notifications/initialized"}),
                &mut conn
            )
            .is_none()
        );
        let bad = handle(&json!({"jsonrpc":"2.0","id":2,"method":"nope"}), &mut conn).unwrap();
        assert_eq!(bad["error"]["code"], -32601);
        let unknown = handle(
            &json!({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"fly"}}),
            &mut conn,
        )
        .unwrap();
        assert_eq!(unknown["result"]["isError"], true);
    }

    #[test]
    fn a_call_crosses_the_socket_and_comes_back() {
        let server = Server::start().unwrap();
        let path = server.path.clone();
        let client = std::thread::spawn(move || {
            let s = UnixStream::connect(&path).unwrap();
            let mut conn = Some((s.try_clone().unwrap(), BufReader::new(s)));
            let req = json!({ "tool": "beat", "args": { "n": 2 } });
            let mut line = String::new();
            let (out, back) = conn.as_mut().unwrap();
            writeln!(out, "{req}").unwrap();
            back.read_line(&mut line).unwrap();
            serde_json::from_str::<Value>(&line).unwrap()
        });
        let req = server.rx.recv_timeout(Duration::from_secs(5)).unwrap();
        assert_eq!(
            (req.tool.as_str(), req.args["n"].as_u64()),
            ("beat", Some(2))
        );
        req.reply.send(json!({ "ok": true, "beat": 2 })).unwrap();
        assert_eq!(client.join().unwrap()["beat"], 2);
    }
}
