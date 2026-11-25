// The AI universe as a directory tree, so Neovim + oil.nvim can browse and edit it
// (screens::universe embeds that nvim through ui::tmux_pane).
//
//   data/universe/
//     compute_semis/                 a primary, from its taxonomy label
//       memory_storage/              a sub-sector under it
//         MU  SNDK  005930.KS ...    one file per member (the file holds its name)
//     funds/                         the ETFs
//     ~grids/                        yours: every directory is a grid of tickers
//       favorites/
//
// Everything except `~grids` is generated from DuckDB each time the screen opens and is
// read-only on disk, so oil refuses to edit the taxonomy: yank names out of it into a grid
// instead. `~grids` is never rewritten; the first open seeds `favorites` from the old list.
//
// oil reports the entry under its cursor to `.cursor` (universe_nvim.lua), a path relative
// to the root such as `compute_semis/memory_storage/MU`; `Tree::locate` turns that back into
// a place on the map.

use std::collections::HashMap;
use std::fs;
use std::io;
use std::os::unix::fs::PermissionsExt;
use std::path::Path;
#[cfg(test)]
use std::path::PathBuf;

/// The writable directory of grids, beside the generated tree.
pub const GRIDS: &str = "~grids";
/// The file oil writes the entry under its cursor to.
pub const CURSOR: &str = ".cursor";
/// The ETFs' directory.
pub const FUNDS: &str = "funds";

/// One basket as the tree sees it: where it sits and what is in it.
pub struct Node<'a> {
    pub level: &'a str,
    pub label: &'a str,
    /// The primary's label, for a sub-sector.
    pub parent: Option<&'a str>,
    pub members: Vec<(&'a str, &'a str)>,
}

/// Where a path in the tree lands on the map.
#[derive(Debug, Clone, PartialEq)]
pub enum Spot {
    /// The groups of a level, with the tile whose value is `pick` selected (a group index,
    /// or a ticker for funds).
    Groups { level: String, pick: Option<String> },
    /// One basket's members (by group index), with `pick` (a ticker) selected.
    Members { group: usize, pick: Option<String> },
}

/// The tree's directories, by path relative to the root, and the group each one is.
#[derive(Default)]
pub struct Tree {
    dirs: HashMap<String, usize>,
    /// The other way: group index -> its directory.
    paths: HashMap<usize, String>,
}

/// `Memory & Storage` -> `memory_storage`: lowercase, runs of anything else become one `_`.
pub fn slug(label: &str) -> String {
    let mut out = String::new();
    for c in label.chars() {
        if c.is_ascii_alphanumeric() {
            out.push(c.to_ascii_lowercase());
        } else if !out.is_empty() && !out.ends_with('_') {
            out.push('_');
        }
    }
    out.trim_end_matches('_').to_string()
}

/// A ticker is safe as a file name when it is plain letters, digits and `.-^=`.
fn safe_name(t: &str) -> bool {
    !t.is_empty()
        && t != "."
        && t != ".."
        && t.chars()
            .all(|c| c.is_ascii_alphanumeric() || ".-^=".contains(c))
}

fn set_mode(p: &Path, mode: u32) -> io::Result<()> {
    fs::set_permissions(p, fs::Permissions::from_mode(mode))
}

/// Makes `p` and everything under it writable again, so it can be removed.
fn unlock(p: &Path) -> io::Result<()> {
    let meta = fs::symlink_metadata(p)?;
    if meta.is_dir() {
        set_mode(p, 0o755)?;
        for e in fs::read_dir(p)? {
            unlock(&e?.path())?;
        }
    }
    Ok(())
}

/// Locks a generated directory: read-only files, directories that can't take new entries.
fn lock(p: &Path) -> io::Result<()> {
    if p.is_dir() {
        for e in fs::read_dir(p)? {
            lock(&e?.path())?;
        }
        set_mode(p, 0o555)
    } else {
        set_mode(p, 0o444)
    }
}

impl Tree {
    /// Writes the generated part of the tree under `root` from `nodes` (index = group index)
    /// and seeds `~grids/favorites` with `favorites` if there are no grids yet.
    pub fn write(root: &Path, nodes: &[Node], favorites: &[&str]) -> io::Result<Tree> {
        fs::create_dir_all(root)?;
        for e in fs::read_dir(root)? {
            let e = e?;
            let name = e.file_name().to_string_lossy().into_owned();
            if name == GRIDS || name.starts_with('.') {
                continue;
            }
            unlock(&e.path())?;
            if e.file_type()?.is_dir() {
                fs::remove_dir_all(e.path())?;
            } else {
                fs::remove_file(e.path())?;
            }
        }
        let mut tree = Tree::default();
        for (i, n) in nodes.iter().enumerate() {
            let rel = match (n.level, n.parent) {
                ("primary", _) => slug(n.label),
                ("sub", Some(p)) => format!("{}/{}", slug(p), slug(n.label)),
                ("fund", _) => FUNDS.to_string(),
                _ => continue,
            };
            let dir = root.join(&rel);
            fs::create_dir_all(&dir)?;
            // A primary's own members live in its sub-sectors; its directory lists only those.
            if n.level != "primary" {
                for (t, name) in &n.members {
                    if safe_name(t) {
                        fs::write(dir.join(t), format!("{name}\n"))?;
                    }
                }
            }
            tree.paths.insert(i, rel.clone());
            tree.dirs.insert(rel, i);
        }
        let grids = root.join(GRIDS);
        if !grids.exists() {
            let fav = grids.join("favorites");
            fs::create_dir_all(&fav)?;
            for t in favorites.iter().filter(|t| safe_name(t)) {
                fs::write(fav.join(t), "")?;
            }
        }
        for e in fs::read_dir(root)? {
            let e = e?;
            let name = e.file_name().to_string_lossy().into_owned();
            if name != GRIDS && !name.starts_with('.') {
                lock(&e.path())?;
            }
        }
        Ok(tree)
    }

    /// The grids in `~grids`: (name, tickers), both sorted. Files that aren't tickers are skipped.
    pub fn grids(root: &Path) -> Vec<(String, Vec<String>)> {
        let Ok(rd) = fs::read_dir(root.join(GRIDS)) else {
            return Vec::new();
        };
        let mut out: Vec<(String, Vec<String>)> = rd
            .flatten()
            .filter(|e| e.file_type().is_ok_and(|t| t.is_dir()))
            .filter_map(|e| {
                let name = e.file_name().to_string_lossy().into_owned();
                if name.starts_with('.') {
                    return None;
                }
                let mut tickers: Vec<String> = fs::read_dir(e.path())
                    .ok()?
                    .flatten()
                    .map(|f| f.file_name().to_string_lossy().into_owned())
                    .filter(|t| safe_name(t))
                    .collect();
                tickers.sort();
                Some((name, tickers))
            })
            .collect();
        out.sort();
        out
    }

    /// Forgets every grid, before they are read in again.
    pub fn clear_grids(&mut self) {
        let prefix = format!("{GRIDS}/");
        self.dirs.retain(|rel, _| !rel.starts_with(&prefix));
        self.paths.retain(|_, rel| !rel.starts_with(&prefix));
    }

    /// Records a grid's directory (`~grids/<name>`) as group `i`.
    pub fn add_grid(&mut self, name: &str, i: usize) {
        let rel = format!("{GRIDS}/{name}");
        self.paths.insert(i, rel.clone());
        self.dirs.insert(rel, i);
    }

    /// The directory of group `i`, relative to the root.
    pub fn path_of(&self, i: usize) -> Option<&str> {
        self.paths.get(&i).map(String::as_str)
    }

    /// Where `rel` (a path oil reported) lands on the map, given each group's level.
    pub fn locate(&self, rel: &str, level_of: impl Fn(usize) -> String) -> Option<Spot> {
        let rel = rel.trim().trim_matches('/');
        if rel.is_empty() {
            return Some(Spot::Groups {
                level: "primary".into(),
                pick: None,
            });
        }
        if rel == GRIDS {
            return Some(Spot::Groups {
                level: "grid".into(),
                pick: None,
            });
        }
        if let Some(&i) = self.dirs.get(rel) {
            let level = level_of(i);
            return Some(match level.as_str() {
                // The funds directory is one group, but the map shows each fund as a tile.
                "fund" => Spot::Groups { level, pick: None },
                _ => Spot::Groups {
                    level,
                    pick: Some(i.to_string()),
                },
            });
        }
        let (dir, name) = rel.rsplit_once('/')?;
        let &i = self.dirs.get(dir)?;
        let level = level_of(i);
        Some(match level.as_str() {
            "fund" => Spot::Groups {
                level,
                pick: Some(name.to_string()),
            },
            _ => Spot::Members {
                group: i,
                pick: Some(name.to_string()),
            },
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn nodes() -> Vec<Node<'static>> {
        vec![
            Node {
                level: "primary",
                label: "Compute & Semis",
                parent: None,
                members: vec![("MU", "Micron")],
            },
            Node {
                level: "sub",
                label: "Memory & Storage",
                parent: Some("Compute & Semis"),
                members: vec![
                    ("MU", "Micron"),
                    ("SNDK", "Sandisk"),
                    ("005930.KS", "Samsung"),
                ],
            },
            Node {
                level: "fund",
                label: "Funds",
                parent: None,
                members: vec![("SOXX", "iShares Semis")],
            },
            Node {
                level: "region",
                label: "US",
                parent: None,
                members: vec![("MU", "Micron")],
            },
        ]
    }

    fn level_of(i: usize) -> String {
        nodes()[i].level.to_string()
    }

    fn tmp(tag: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("fl-universe-fs-{tag}-{}", std::process::id()));
        if d.exists() {
            unlock(&d).unwrap();
            fs::remove_dir_all(&d).unwrap();
        }
        d
    }

    #[test]
    fn slugs_read_like_directory_names() {
        assert_eq!(slug("Memory & Storage"), "memory_storage");
        assert_eq!(slug("Compute & Semis"), "compute_semis");
        assert_eq!(slug("Edge, RF & Logic Semis"), "edge_rf_logic_semis");
        assert_eq!(
            slug("3D Printing & On-Demand Mfg"),
            "3d_printing_on_demand_mfg"
        );
    }

    #[test]
    fn writes_the_taxonomy_read_only_and_keeps_grids() {
        let root = tmp("write");
        let tree = Tree::write(&root, &nodes(), &["NVDA", "MU"]).unwrap();
        let mem = root.join("compute_semis/memory_storage");
        assert_eq!(fs::read_to_string(mem.join("MU")).unwrap(), "Micron\n");
        assert!(mem.join("005930.KS").exists());
        assert!(root.join("funds/SOXX").exists());
        assert!(!root.join("us").exists(), "regions are not directories");
        assert!(
            fs::write(mem.join("NEW"), "").is_err(),
            "the taxonomy is read-only"
        );
        assert_eq!(tree.path_of(1), Some("compute_semis/memory_storage"));

        // A grid edit survives the next write; the taxonomy is rebuilt over its lock.
        fs::write(root.join(GRIDS).join("favorites/AMD"), "").unwrap();
        Tree::write(&root, &nodes(), &[]).unwrap();
        let grids = Tree::grids(&root);
        assert_eq!(
            grids,
            vec![(
                "favorites".into(),
                vec!["AMD".into(), "MU".into(), "NVDA".into()]
            )]
        );
        unlock(&root).unwrap();
        fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn oil_paths_land_on_the_map() {
        let root = tmp("locate");
        let mut tree = Tree::write(&root, &nodes(), &[]).unwrap();
        tree.add_grid("core", 9);
        let lv = |i: usize| {
            if i == 9 {
                "grid".to_string()
            } else {
                level_of(i)
            }
        };
        let groups = |level: &str, pick: Option<&str>| Spot::Groups {
            level: level.into(),
            pick: pick.map(String::from),
        };
        // Inside the memory directory on MU: that basket's members, MU picked.
        assert_eq!(
            tree.locate("compute_semis/memory_storage/MU", lv),
            Some(Spot::Members {
                group: 1,
                pick: Some("MU".into())
            })
        );
        // On the memory directory inside its primary: the sub-sector map, memory picked.
        assert_eq!(
            tree.locate("compute_semis/memory_storage", lv),
            Some(groups("sub", Some("1")))
        );
        assert_eq!(
            tree.locate("compute_semis", lv),
            Some(groups("primary", Some("0")))
        );
        assert_eq!(tree.locate("", lv), Some(groups("primary", None)));
        assert_eq!(
            tree.locate("funds/SOXX", lv),
            Some(groups("fund", Some("SOXX")))
        );
        assert_eq!(tree.locate("~grids", lv), Some(groups("grid", None)));
        assert_eq!(
            tree.locate("~grids/core", lv),
            Some(groups("grid", Some("9")))
        );
        assert_eq!(
            tree.locate("~grids/core/SPY", lv),
            Some(Spot::Members {
                group: 9,
                pick: Some("SPY".into())
            })
        );
        assert_eq!(tree.locate("nowhere/at/all", lv), None);
        unlock(&root).unwrap();
        fs::remove_dir_all(&root).unwrap();
    }
}
