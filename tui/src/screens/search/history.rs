// Query history for the search input (↑ / ↓ while the input has focus),
// shell-style: ↑ walks back from the newest, ↓ walks forward and finally
// restores what was being typed. Persisted one query per line, newest last,
// at ~/.local/share/nvim/finlarp/search_history. IO failures only
// cost persistence, never the screen.

use std::path::PathBuf;

const MAX: usize = 500;

#[derive(Debug, Default)]
pub struct History {
    path: Option<PathBuf>,
    items: Vec<String>,
    /// Index into `items` while browsing; None = editing the draft.
    pos: Option<usize>,
    draft: String,
}

impl History {
    pub fn load() -> Self {
        let path = std::env::var_os("HOME")
            .map(|h| PathBuf::from(h).join(".local/share/nvim/finlarp/search_history"));
        let items = path
            .as_ref()
            .and_then(|p| std::fs::read_to_string(p).ok())
            .map(|s| {
                s.lines()
                    .filter(|l| !l.trim().is_empty())
                    .map(str::to_string)
                    .collect()
            })
            .unwrap_or_default();
        Self {
            path,
            items,
            ..Self::default()
        }
    }

    #[cfg(test)]
    pub fn in_memory(items: &[&str]) -> Self {
        Self {
            items: items.iter().map(|s| s.to_string()).collect(),
            ..Self::default()
        }
    }

    /// Older entry; `current` is kept as the draft when browsing starts.
    pub fn prev(&mut self, current: &str) -> Option<String> {
        let i = match self.pos {
            None if self.items.is_empty() => return None,
            None => {
                self.draft = current.to_string();
                self.items.len() - 1
            }
            Some(0) => return None,
            Some(i) => i - 1,
        };
        self.pos = Some(i);
        self.items.get(i).cloned()
    }

    /// Newer entry, then the draft.
    pub fn next(&mut self) -> Option<String> {
        let i = self.pos?;
        if i + 1 < self.items.len() {
            self.pos = Some(i + 1);
            self.items.get(i + 1).cloned()
        } else {
            self.pos = None;
            Some(std::mem::take(&mut self.draft))
        }
    }

    /// Typing leaves browse mode.
    pub fn reset(&mut self) {
        self.pos = None;
    }

    pub fn push(&mut self, q: &str) {
        let q = q.trim();
        if q.is_empty() {
            return;
        }
        self.items.retain(|x| x != q);
        self.items.push(q.to_string());
        let over = self.items.len().saturating_sub(MAX);
        self.items.drain(..over);
        self.pos = None;
        if let Some(p) = &self.path {
            if let Some(dir) = p.parent() {
                let _ = std::fs::create_dir_all(dir);
            }
            let _ = std::fs::write(p, self.items.join("\n") + "\n");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn browses_and_restores_draft() {
        let mut h = History::in_memory(&["a", "b"]);
        assert_eq!(h.prev("draft").as_deref(), Some("b"));
        assert_eq!(h.prev("b").as_deref(), Some("a"));
        assert_eq!(h.prev("a"), None);
        assert_eq!(h.next().as_deref(), Some("b"));
        assert_eq!(h.next().as_deref(), Some("draft"));
        assert_eq!(h.next(), None);
        h.push("a");
        assert_eq!(h.prev("").as_deref(), Some("a"));
        assert_eq!(h.prev("").as_deref(), Some("b"));
    }
}
