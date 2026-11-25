// Every Claude chat fl starts, in one place: `<space>ac` (the popup), `C` in the x
// diagrams, the Z chats (one per mode) and the chat screen all record themselves here
// (data/chats.json) when Claude hands back a session id and again when a turn ends.
// The `L` screen lists them, newest first, with their metadata, and resumes any of them.
//
// One entry per Claude session id. The file is read, changed and written whole on every
// record; chats record a few times a turn at most, so that is cheap. A missing or broken
// file reads as no chats.

use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

/// Overrides the registry path (tests).
pub const FILE_ENV: &str = "FL_CHATS_FILE";
/// Oldest entries drop off past this many.
const MAX: usize = 500;

#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct Entry {
    /// Claude Code session id (resume with `claude --resume <id>`).
    pub session: String,
    /// Where it was started: "ac", "x diagrams", "z:<mode>", "chat".
    pub source: String,
    /// First thing asked, cut short.
    #[serde(default)]
    pub title: String,
    /// Folder Claude ran in (resume must run there too).
    #[serde(default)]
    pub cwd: String,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub turns: u32,
    #[serde(default)]
    pub cost: f64,
    #[serde(default)]
    pub input: u64,
    #[serde(default)]
    pub output: u64,
    /// fl's own copy of the conversation, when it keeps one (Z).
    #[serde(default)]
    pub file: Option<String>,
    /// Seconds since the epoch, first and last recorded.
    #[serde(default)]
    pub started: u64,
    #[serde(default)]
    pub updated: u64,
}

/// What a chat knows when it records itself; empty fields leave the entry's as they were.
#[derive(Clone, Debug, Default)]
pub struct Note<'a> {
    pub session: &'a str,
    pub source: &'a str,
    pub title: &'a str,
    pub model: Option<&'a str>,
    pub file: Option<&'a str>,
    /// This turn's usage, added to the entry's totals.
    pub turn: Option<(f64, u64, u64)>,
}

pub fn path() -> PathBuf {
    std::env::var_os(FILE_ENV)
        .map(PathBuf::from)
        .unwrap_or_else(|| crate::data_dir().join("chats.json"))
}

fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Every chat, newest first.
pub fn load() -> Vec<Entry> {
    let mut v: Vec<Entry> = std::fs::read_to_string(path())
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default();
    v.sort_by(|a, b| b.updated.cmp(&a.updated));
    v
}

fn store(v: &[Entry]) {
    let p = path();
    if let Some(d) = p.parent() {
        let _ = std::fs::create_dir_all(d);
    }
    let tmp = p.with_extension("json.tmp");
    if std::fs::write(&tmp, serde_json::to_string_pretty(v).unwrap_or_default()).is_ok() {
        let _ = std::fs::rename(tmp, p);
    }
}

/// Adds or updates the chat with `n.session`.
pub fn record(n: Note) {
    if n.session.is_empty() {
        return;
    }
    // tests never touch the real registry
    #[cfg(test)]
    if std::env::var_os(FILE_ENV).is_none() {
        return;
    }
    let mut v = load();
    let t = now();
    let i = match v.iter().position(|e| e.session == n.session) {
        Some(i) => i,
        None => {
            v.push(Entry {
                session: n.session.to_string(),
                started: t,
                cwd: std::env::current_dir()
                    .map(|d| d.to_string_lossy().into_owned())
                    .unwrap_or_default(),
                ..Entry::default()
            });
            v.len() - 1
        }
    };
    let e = &mut v[i];
    if !n.source.is_empty() {
        e.source = n.source.to_string();
    }
    if e.title.is_empty() && !n.title.trim().is_empty() {
        e.title = short(n.title);
    }
    if let Some(m) = n.model {
        e.model = Some(m.to_string());
    }
    if let Some(f) = n.file {
        e.file = Some(f.to_string());
    }
    if let Some((cost, input, output)) = n.turn {
        e.turns += 1;
        e.cost += cost;
        e.input += input;
        e.output += output;
    }
    e.updated = t;
    v.sort_by(|a, b| b.updated.cmp(&a.updated));
    v.truncate(MAX);
    store(&v);
}

/// Forgets one chat (its Claude transcript stays).
pub fn forget(session: &str) {
    let mut v = load();
    v.retain(|e| e.session != session);
    store(&v);
}

/// First line, whitespace squeezed, at most 120 characters.
fn short(s: &str) -> String {
    let one = s.split_whitespace().collect::<Vec<_>>().join(" ");
    one.chars().take(120).collect()
}

/// A fresh session id for a chat fl starts itself (`claude --session-id`).
pub fn new_id() -> String {
    let mut b = [0u8; 16];
    let ok = std::fs::File::open("/dev/urandom")
        .and_then(|mut f| std::io::Read::read_exact(&mut f, &mut b))
        .is_ok();
    if !ok {
        let n = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0)
            ^ (std::process::id() as u128) << 64;
        b = n.to_le_bytes();
    }
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    let h: String = b.iter().map(|x| format!("{x:02x}")).collect();
    format!(
        "{}-{}-{}-{}-{}",
        &h[0..8],
        &h[8..12],
        &h[12..16],
        &h[16..20],
        &h[20..32]
    )
}

#[cfg(test)]
pub fn test_file(name: &str) -> PathBuf {
    let p = std::env::temp_dir().join(format!("fl-chats-{name}-{}.json", std::process::id()));
    let _ = std::fs::remove_file(&p);
    p
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn records_merge_by_session_and_sum_usage() {
        let p = test_file("merge");
        // SAFETY: single test touches this env var; other tests set their own before use
        unsafe { std::env::set_var(FILE_ENV, &p) };
        record(Note {
            session: "s1",
            source: "z:explain",
            title: "why   is HBM\nhot",
            ..Note::default()
        });
        record(Note {
            session: "s1",
            source: "z:explain",
            title: "later question",
            model: Some("opus"),
            turn: Some((0.5, 100, 10)),
            ..Note::default()
        });
        record(Note {
            session: "s1",
            source: "z:explain",
            turn: Some((0.25, 50, 5)),
            ..Note::default()
        });
        let v = load();
        let e = v.iter().find(|e| e.session == "s1").unwrap();
        assert_eq!(e.title, "why is HBM hot");
        assert_eq!(e.model.as_deref(), Some("opus"));
        assert_eq!((e.turns, e.input, e.output), (2, 150, 15));
        assert!((e.cost - 0.75).abs() < 1e-9);
        forget("s1");
        assert!(load().iter().all(|e| e.session != "s1"));
        let id = new_id();
        assert_eq!(id.len(), 36);
        assert!(id.chars().all(|c| c.is_ascii_hexdigit() || c == '-'));
        let _ = std::fs::remove_file(p);
    }
}
