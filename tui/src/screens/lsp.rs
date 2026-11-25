// The diagram LSP's term index: what the filing reader can "go to definition" on.
//
// The terms are py/derive/lsp_terms_seed.json (compiled in), each with the spellings filings
// use for it and the x-diagrams node that explains it. py/derive/lsp_terms.py counts them over
// every parsed filing into data/lsp/terms.json (filings, tickers, top tickers), which is read
// too when present. Matching is whole-word: acronyms (any capital in the spelling) match
// case-sensitively so "SiC" never fires on "sic"; other spellings ignore case.
//
// The reader asks two things: every term on a line (to underline them), and the term under
// the cursor (for gd / gr / K).

use std::sync::OnceLock;

use serde::Deserialize;

const SEED: &str = include_str!("../../../py/derive/lsp_terms_seed.json");

#[derive(Clone, Debug, Default, Deserialize)]
pub struct Term {
    pub term: String,
    #[serde(default)]
    pub aliases: Vec<String>,
    /// The x-diagrams node that explains it (None: a gap, no diagram yet).
    #[serde(default)]
    pub node: Option<String>,
    #[serde(default)]
    pub kind: String,
    /// From data/lsp/terms.json, when the scan has run.
    #[serde(default)]
    pub docs: u64,
    #[serde(default)]
    pub tickers: u64,
    #[serde(default)]
    pub top: Vec<String>,
}

/// One spelling to look for.
struct Spelling {
    text: String,
    /// Lowercased when the match ignores case.
    folded: bool,
    term: usize,
}

pub struct Index {
    pub terms: Vec<Term>,
    /// Longest first, so "high bandwidth memory" wins over "memory".
    spellings: Vec<Spelling>,
}

/// A term found on a line: char offsets [start, end) and which term.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Hit {
    pub start: usize,
    pub end: usize,
    pub term: usize,
}

impl Index {
    pub fn from_terms(terms: Vec<Term>) -> Self {
        let mut spellings = Vec::new();
        for (i, t) in terms.iter().enumerate() {
            for s in std::iter::once(&t.term).chain(&t.aliases) {
                let s = s.trim();
                if s.chars().count() < 2 {
                    continue;
                }
                let exact = s.chars().any(|c| c.is_uppercase() || c.is_ascii_digit());
                spellings.push(Spelling {
                    text: if exact { s.to_string() } else { s.to_lowercase() },
                    folded: !exact,
                    term: i,
                });
            }
        }
        spellings.sort_by(|a, b| b.text.chars().count().cmp(&a.text.chars().count()));
        Self { terms, spellings }
    }

    /// The seed, with the scan's counts merged in when data/lsp/terms.json exists.
    pub fn load() -> Self {
        let mut terms: Vec<Term> = serde_json::from_str(SEED).unwrap_or_default();
        let stats: Vec<Term> = std::fs::read_to_string(crate::data_dir().join("lsp/terms.json"))
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default();
        for t in terms.iter_mut() {
            if let Some(s) = stats.iter().find(|s| s.term == t.term) {
                t.docs = s.docs;
                t.tickers = s.tickers;
                t.top = s.top.clone();
            }
        }
        Self::from_terms(terms)
    }

    /// Every term on `line`, left to right, not overlapping.
    pub fn hits(&self, line: &str) -> Vec<Hit> {
        let chars: Vec<char> = line.chars().collect();
        let lower: Vec<char> = line.to_lowercase().chars().collect();
        // to_lowercase can change the length (rare non-ASCII); fall back to exact only
        let lower = (lower.len() == chars.len()).then_some(lower);
        let mut taken = vec![false; chars.len()];
        let mut out = Vec::new();
        for sp in &self.spellings {
            let hay: &[char] = match (&lower, sp.folded) {
                (Some(l), true) => l,
                (None, true) => continue,
                _ => &chars,
            };
            let needle: Vec<char> = sp.text.chars().collect();
            let n = needle.len();
            if n == 0 || n > hay.len() {
                continue;
            }
            let mut i = 0;
            while i + n <= hay.len() {
                if hay[i..i + n] == needle[..]
                    && boundary(&chars, i.wrapping_sub(1))
                    && boundary(&chars, i + n)
                    && !taken[i..i + n].iter().any(|&t| t)
                {
                    taken[i..i + n].iter_mut().for_each(|t| *t = true);
                    out.push(Hit {
                        start: i,
                        end: i + n,
                        term: sp.term,
                    });
                    i += n;
                } else {
                    i += 1;
                }
            }
        }
        out.sort_by_key(|h| h.start);
        out
    }

    /// The term covering char column `col` of `line` (or touching it, at a word's end).
    pub fn at(&self, line: &str, col: usize) -> Option<Hit> {
        let hits = self.hits(line);
        hits.iter()
            .find(|h| h.start <= col && col < h.end)
            .or_else(|| hits.iter().find(|h| h.end == col))
            .copied()
    }
}

/// True when char `i` is outside the line or not part of a word.
fn boundary(chars: &[char], i: usize) -> bool {
    chars
        .get(i)
        .is_none_or(|c| !(c.is_alphanumeric() || *c == '_' || *c == '-'))
}

/// The process-wide index, loaded on first use.
pub fn index() -> &'static Index {
    static IDX: OnceLock<Index> = OnceLock::new();
    IDX.get_or_init(Index::load)
}

/// The search query `gr` runs for a term: the term itself, quoted when it is several words.
pub fn refs_query(t: &Term) -> String {
    if t.term.contains(' ') {
        format!("\"{}\"", t.term)
    } else {
        t.term.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn idx() -> Index {
        Index::from_terms(serde_json::from_str(SEED).unwrap())
    }

    #[test]
    fn seed_parses_and_every_node_is_a_real_page() {
        let i = idx();
        assert!(i.terms.len() > 50);
        let pages = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src/screens/diagrams_pages");
        for t in &i.terms {
            if let Some(n) = &t.node {
                assert!(pages.join(format!("{n}.txt")).is_file() || pages.join(format!("terms/{n}.txt")).is_file(), "{}: no page {n}", t.term);
            }
        }
    }

    #[test]
    fn finds_terms_whole_word_and_respects_acronym_case() {
        let i = idx();
        let line = "Demand for HBM3E and high bandwidth memory grew; sic transit, but SiC wafers too.";
        let names: Vec<&str> = i.hits(line).iter().map(|h| i.terms[h.term].term.as_str()).collect();
        assert_eq!(names, vec!["HBM", "HBM", "SiC", "wafer"]);
        // "memory" alone is not a term; "HBMs" is not a whole-word HBM
        assert!(i.hits("HBMs memory").is_empty());
        let h = i.at(line, 12).unwrap();
        assert_eq!(i.terms[h.term].term, "HBM");
        assert_eq!(i.terms[h.term].node.as_deref(), Some("MEM_HBM_STACK"));
        assert!(i.at(line, 0).is_none());
    }

    #[test]
    fn refs_query_quotes_phrases() {
        let i = idx();
        let hbm = i.terms.iter().find(|t| t.term == "HBM").unwrap();
        assert_eq!(refs_query(hbm), "HBM");
        let cpo = i.terms.iter().find(|t| t.term == "co-packaged optics").unwrap();
        assert_eq!(refs_query(cpo), "\"co-packaged optics\"");
    }
}
