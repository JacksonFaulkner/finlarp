// AI-universe browser (ai_universe / ai_universe_category, loaded from
// data/ai_stocks_reviewed.json by db.load_universe). No argument: pick a
// group (primary bucket, sub bucket or region). "level|category": pick a
// member, which opens its dossier.

use std::io;

use crate::app::Ctx;
use crate::screens::pick::{Item, Pick};

const GROUPS_SQL: &str = "
    SELECT 'primary' AS level, c.category, NULL AS parent, count(*) AS n,
           list(u.ticker ORDER BY c.weight DESC, u.ticker) AS tickers
    FROM ai_universe_category c JOIN ai_universe u USING (ticker)
    WHERE c.level = 'primary' AND u.eligible IS DISTINCT FROM false
    GROUP BY c.category
    UNION ALL
    SELECT 'sub', c.category, t.primary_category, count(*),
           list(u.ticker ORDER BY c.weight DESC, u.ticker)
    FROM ai_universe_category c
    JOIN ai_universe u USING (ticker)
    LEFT JOIN ai_taxonomy t ON t.sub_category = c.category
    WHERE c.level = 'sub' AND u.eligible IS DISTINCT FROM false
    GROUP BY c.category, t.primary_category
    UNION ALL
    SELECT 'region', region, NULL, count(*), list(ticker ORDER BY ticker)
    FROM ai_universe WHERE eligible IS DISTINCT FROM false
    GROUP BY region
    ORDER BY 1, 3 NULLS FIRST, 4 DESC";

const NOT_LOADED: &str = "The AI universe isn't loaded into DuckDB yet.\n\n  \
    python -c 'from core import db; db.load_universe()'   (from the repo root)";

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Pick> {
    let res = match arg.as_deref().and_then(|a| a.split_once('|')) {
        Some((level, category)) => members(ctx, level, category),
        None => groups(ctx),
    };
    Ok(match res {
        Ok(p) => p,
        Err(e) => Pick::new("Universe", "universe", Vec::new(), false, &e, ctx.theme),
    })
}

/// Reads with `f`; if the tables are empty or missing, has Python load the
/// universe JSON once and retries.
fn with_load<T>(
    ctx: &Ctx,
    f: impl Fn(&duckdb::Connection) -> Result<Vec<T>, String>,
) -> Result<Vec<T>, String> {
    let read = |ctx: &Ctx| f(&crate::db::open_read_only(&ctx.db_path)?);
    if let Ok(rows) = read(ctx)
        && !rows.is_empty()
    {
        return Ok(rows);
    }
    crate::pyrun::run_code("from core import db; db.load_universe()")?;
    let rows = read(ctx)?;
    if rows.is_empty() {
        Err(NOT_LOADED.to_string())
    } else {
        Ok(rows)
    }
}

fn groups(ctx: &Ctx) -> Result<Pick, String> {
    let rows = with_load(ctx, |conn| {
        let mut stmt = conn.prepare(GROUPS_SQL).map_err(|e| e.to_string())?;
        let rows = stmt
            .query_map([], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, Option<String>>(2)?,
                    r.get::<_, i64>(3)?,
                    r.get::<_, duckdb::types::Value>(4)?,
                ))
            })
            .map_err(|e| e.to_string())?;
        Ok(rows.flatten().collect())
    })?;
    let items = rows
        .into_iter()
        .map(|(level, category, parent, n, tickers)| {
            let tickers = list_of_strings(&tickers).join(" ");
            let label = match level.as_str() {
                "primary" => format!("{category}  {n}  [primary]"),
                "sub" => format!("  {category}  {n}  {}", parent.unwrap_or_default()),
                _ => format!("{category}  {n}  [region]"),
            };
            Item {
                label,
                detail: tickers,
                value: format!("{level}|{category}"),
            }
        })
        .collect();
    Ok(Pick::new(
        "AI universe",
        "universe",
        items,
        false,
        NOT_LOADED,
        ctx.theme,
    ))
}

fn members(ctx: &Ctx, level: &str, category: &str) -> Result<Pick, String> {
    let (level, category) = (level.to_string(), category.to_string());
    let rows = with_load(ctx, |conn| {
        let (sql, params): (&str, Vec<&str>) = if level == "region" {
            (
                "SELECT ticker, name, 1.0::DOUBLE FROM ai_universe \
                 WHERE region = ? AND eligible IS DISTINCT FROM false ORDER BY ticker",
                vec![category.as_str()],
            )
        } else {
            (
                "SELECT u.ticker, u.name, c.weight FROM ai_universe_category c \
                 JOIN ai_universe u USING (ticker) \
                 WHERE c.level = ? AND c.category = ? AND u.eligible IS DISTINCT FROM false \
                 ORDER BY c.weight DESC, u.ticker",
                vec![level.as_str(), category.as_str()],
            )
        };
        let mut stmt = conn.prepare(sql).map_err(|e| e.to_string())?;
        let rows = stmt
            .query_map(duckdb::params_from_iter(params), |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, Option<String>>(1)?,
                    r.get::<_, Option<f64>>(2)?,
                ))
            })
            .map_err(|e| e.to_string())?;
        Ok(rows.flatten().collect())
    })?;
    let items = rows
        .into_iter()
        .map(|(ticker, name, weight)| Item {
            label: ticker.clone(),
            detail: match (name, level.as_str()) {
                (Some(n), "region") => n,
                (Some(n), _) => format!("{n}  {:.0}%", weight.unwrap_or(0.0) * 100.0),
                (None, _) => String::new(),
            },
            value: ticker,
        })
        .collect();
    Ok(Pick::new(
        &category, "dossier", items, false, NOT_LOADED, ctx.theme,
    ))
}

fn list_of_strings(v: &duckdb::types::Value) -> Vec<String> {
    match v {
        duckdb::types::Value::List(items) | duckdb::types::Value::Array(items) => items
            .iter()
            .filter_map(|x| match x {
                duckdb::types::Value::Text(s) => Some(s.clone()),
                _ => None,
            })
            .collect(),
        _ => Vec::new(),
    }
}
