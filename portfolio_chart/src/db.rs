// Read-only DuckDB access to the plugin's cache (written by the Python side).

use std::path::Path;
use std::thread::sleep;
use std::time::Duration;

/// Opens `path` read-only. DuckDB allows one read-write process *or* any
/// number of readers, and the Python jobs nvim fires (live positions,
/// canslim/dossier rebuilds) hold the write lock for a moment; retry for
/// ~2s instead of failing the screen (dossier has no reload key).
pub fn open_read_only(path: &Path) -> Result<duckdb::Connection, String> {
    let mut last = String::new();
    for attempt in 0..20 {
        let cfg = duckdb::Config::default()
            .access_mode(duckdb::AccessMode::ReadOnly)
            .map_err(|e| e.to_string())?;
        match duckdb::Connection::open_with_flags(path, cfg) {
            Ok(conn) => return Ok(conn),
            Err(e) => {
                last = e.to_string();
                if !last.to_lowercase().contains("lock") {
                    break;
                }
                sleep(Duration::from_millis(50 + 10 * attempt));
            }
        }
    }
    Err(format!("can't open {}: {last}", path.display()))
}
