// Shared data model for every screen: a value is only ever shown together
// with where it came from. This mirrors the JSON services/dossier.py writes
// (see its module docstring); CANSLIM and search produce the same shapes so
// one set of components (src/ui) renders and audits all of them.
//
//   Source  — a document URL (optionally with a #:~:text= quote fragment),
//             or a formula plus the Sources of its inputs.
//   Block   — a renderable unit: table / kv / series / bars / text. Every
//             row, cell group, point or bar carries its own Source.
//   Section — a titled list of Blocks (one entry in a screen's nav list).

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct Source {
    pub label: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub url: Option<String>,
    /// Present on computed values ("2,739.3 / 2,006.1 - 1").
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub formula: Option<String>,
    /// Sources of the formula's operands; may nest.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub inputs: Vec<Source>,
}

impl Source {
    pub fn url(label: impl Into<String>, url: impl Into<String>) -> Self {
        Self { label: label.into(), url: Some(url.into()), ..Default::default() }
    }

    pub fn derived(label: impl Into<String>, formula: impl Into<String>, inputs: Vec<Source>) -> Self {
        Self { label: label.into(), formula: Some(formula.into()), inputs, ..Default::default() }
    }

    pub fn is_derived(&self) -> bool {
        self.formula.is_some()
    }

    /// URL without the `#:~:text=` quote fragment.
    pub fn doc_url(&self) -> Option<&str> {
        self.url.as_deref().map(|u| u.split("#:~:text=").next().unwrap_or(u))
    }

    /// Decoded quote from the `#:~:text=` fragment, if any.
    pub fn quote(&self) -> Option<String> {
        let frag = self.url.as_deref()?.split("#:~:text=").nth(1)?;
        let frag = frag.split(['&', ',']).next()?;
        let bytes = frag.as_bytes();
        let mut out = Vec::with_capacity(bytes.len());
        let mut i = 0;
        while i < bytes.len() {
            // decode from bytes, not &str slices: a raw non-ASCII char after '%' would split a UTF-8 boundary
            let hex = bytes.get(i + 1..i + 3).and_then(|h| std::str::from_utf8(h).ok());
            if bytes[i] == b'%'
                && let Some(b) = hex.and_then(|h| u8::from_str_radix(h, 16).ok())
            {
                out.push(b);
                i += 3;
                continue;
            }
            out.push(bytes[i]);
            i += 1;
        }
        String::from_utf8(out).ok()
    }
}

/// A table row: cells left to right, one Source for the row.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Row {
    pub cells: Vec<String>,
    /// Flagged as recent (< 30 days) by the producer; drawn with a ● marker.
    #[serde(default)]
    pub new: bool,
    #[serde(default)]
    pub src: Option<Source>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct KvRow {
    pub label: String,
    pub value: String,
    #[serde(default)]
    pub new: bool,
    #[serde(default)]
    pub src: Option<Source>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Point {
    pub x: String,
    /// None = missing observation (drawn as a gap, never as zero).
    pub y: Option<f64>,
    #[serde(default)]
    pub src: Option<Source>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BarItem {
    pub label: String,
    pub value: f64,
    /// Optional comparison value drawn beside `value` (e.g. EPS estimate vs actual).
    #[serde(default)]
    pub compare: Option<f64>,
    #[serde(default)]
    pub src: Option<Source>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum Block {
    Table {
        #[serde(default)]
        title: String,
        cols: Vec<String>,
        rows: Vec<Row>,
    },
    Kv {
        #[serde(default)]
        title: String,
        rows: Vec<KvRow>,
    },
    Series {
        #[serde(default)]
        title: String,
        #[serde(default)]
        unit: String,
        points: Vec<Point>,
    },
    Bars {
        #[serde(default)]
        title: String,
        #[serde(default)]
        unit: String,
        items: Vec<BarItem>,
    },
    Text {
        #[serde(default)]
        title: String,
        text: String,
        #[serde(default)]
        src: Option<Source>,
    },
}

impl Block {
    pub fn title(&self) -> &str {
        match self {
            Block::Table { title, .. }
            | Block::Kv { title, .. }
            | Block::Series { title, .. }
            | Block::Bars { title, .. }
            | Block::Text { title, .. } => title,
        }
    }

    /// Number of selectable items (rows / points / bars; text = 1).
    pub fn len(&self) -> usize {
        match self {
            Block::Table { rows, .. } => rows.len(),
            Block::Kv { rows, .. } => rows.len(),
            Block::Series { points, .. } => points.len(),
            Block::Bars { items, .. } => items.len(),
            Block::Text { .. } => 1,
        }
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Source of the i-th selectable item.
    pub fn source(&self, i: usize) -> Option<&Source> {
        match self {
            Block::Table { rows, .. } => rows.get(i)?.src.as_ref(),
            Block::Kv { rows, .. } => rows.get(i)?.src.as_ref(),
            Block::Series { points, .. } => points.get(i)?.src.as_ref(),
            Block::Bars { items, .. } => items.get(i)?.src.as_ref(),
            Block::Text { src, .. } => src.as_ref(),
        }
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Section {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub blocks: Vec<Block>,
    /// Section contains something flagged new.
    #[serde(default)]
    pub new: bool,
    /// Short right-aligned note in the nav list ("3 new", "A+").
    #[serde(default)]
    pub badge: String,
}

impl Section {
    /// Every Source in the section in display order: the audit view groups these by document.
    pub fn sources(&self) -> impl Iterator<Item = &Source> {
        self.blocks.iter().flat_map(|b| (0..b.len()).filter_map(move |i| b.source(i)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quote_decodes_fragment() {
        let s = Source::url("x", "https://a/b.htm#:~:text=Q2%20Net%20Revenue%3A%20%242.739");
        assert_eq!(s.quote().as_deref(), Some("Q2 Net Revenue: $2.739"));
        assert_eq!(s.doc_url(), Some("https://a/b.htm"));
    }

    #[test]
    fn quote_survives_non_ascii_and_truncated_escapes() {
        let s = Source::url("x", "https://a#:~:text=caf%é%2");
        assert_eq!(s.quote().as_deref(), Some("caf%é%2"));
    }
}
