"""AI-universe taxonomy v3: primary layers (in stack order), sub-sectors, display labels, and the
one-shot migration from the v2 keys. Keys are stable ids; labels are what the UI shows.

    cd py && uv run python -m core.taxonomy          # migrate DuckDB + data/ai_stocks_reviewed.json
"""
from __future__ import annotations

import json
from pathlib import Path

# primary -> (label, {sub: (label, description)}) in display order (silicon -> systems -> power -> software -> apps)
TAXONOMY: dict[str, tuple[str, dict[str, tuple[str, str]]]] = {
    "compute_hardware": ("Compute & Semis", {
        "processors_accelerators": ("Processors & AI Accelerators", "GPUs, custom AI ASICs and their design services, CPUs and processor IP."),
        "edge_rf_semis": ("Edge, RF & Logic Semis", "RF/wireless, mixed-signal, FPGA, edge-SoC and semiconductor IP."),
        "analog_power_semis": ("Analog & Power Semis", "Analog, power-management, wide-bandgap and microcontroller silicon."),
        "interconnect_semiconductors": ("Interconnect Silicon", "Connectivity silicon, retimers, switches, DSPs and memory-interface IP; not operation of a network."),
        "memory_storage": ("Memory & Storage", "Memory/storage media, enterprise storage systems and storage-enabling products; not necessarily AI-only."),
        "foundry_packaging": ("Foundry & Packaging", "Wafer foundries and advanced packaging/test outsourcers."),
        "semicap_materials": ("Semicap, Materials & Test", "Wafer-fab equipment, wafer substrates/process materials, and electronic/optical test and measurement."),
        "optical_photonics": ("Optical & Photonics", "Optical components, lasers and photonics for data-center links."),
        "devices_ems_distribution": ("Devices, EMS & Distribution", "PCs and end-user devices with on-device AI, contract manufacturers and electronics distributors."),
        "quantum_computing": ("Quantum Computing", "Quantum computing hardware and systems; adjacency to AI does not establish AI commercial materiality."),
    }),
    "infrastructure": ("Data Center & Network", {
        "cloud_platforms": ("Cloud & Edge Platforms", "Hyperscale clouds plus CDN/edge compute services."),
        "neocloud_gpu_hosting": ("Neoclouds & GPU Hosting", "GPU-rental clouds and miners converting capacity to AI hosting."),
        "datacenter_operators": ("Data Center & Tower Operators", "Data-center owners/operators/colocation (REIT or not) and communications tower REITs."),
        "servers_systems": ("Servers & Systems", "Server OEMs/ODMs and rack-scale system builders."),
        "networking_connectivity": ("Networking & Connectivity", "Switches, routers, optical transport, cabling and carrier connectivity."),
        "electrical_cooling_equipment": ("Power & Cooling Equipment", "Power distribution/conversion, protection/control, HVAC/thermal equipment and components."),
        "engineering_construction": ("Engineering & Construction", "Contractors and engineers building data centers and the grid around them."),
    }),
    "energy": ("Power & Energy", {
        "power_utilities": ("Utilities & Power Producers", "Regulated utilities and independent power producers."),
        "power_equipment": ("Generation & Storage Equipment", "Generators, turbines, fuel cells and stationary energy storage."),
        "nuclear": ("Nuclear", "Fuel enrichment/mining, reactor technology and nuclear components and services."),
        "natural_gas": ("Natural Gas", "Gas production and midstream pipelines."),
    }),
    "software_platform": ("Software & Platforms", {
        "data_ai_platforms": ("Data & AI Platforms", "AI platforms, data warehouses/databases, search and analytics infrastructure software."),
        "devtools_observability": ("DevOps & Observability", "Developer tooling, workflow automation and monitoring/observability."),
        "cybersecurity": ("Cybersecurity", "Security software and network security."),
        "enterprise_saas": ("Enterprise Software", "Enterprise applications, collaboration and connected-operations software."),
        "design_simulation_eda": ("Design & EDA Software", "Chip/engineering design, simulation and CAD."),
    }),
    "applications": ("Applications & Services", {
        "adtech_marketing": ("Adtech & Marketing", "Advertising platforms, measurement and marketing software."),
        "consumer_commerce_mobility": ("Commerce & Mobility", "E-commerce, marketplaces, ride-hailing, travel and local services."),
        "social_media_streaming": ("Social, Media & Streaming", "Social networks, search/ad-funded media, video, music and dating."),
        "gaming": ("Gaming", "Game publishers, platforms and engines."),
        "healthcare": ("Healthcare", "Diagnostics, medtech, digital health and AI drug discovery."),
        "payments_lending": ("Payments & Lending", "Card networks, payment processors and acquirers, and digital lending."),
        "fintech_software": ("Fintech Software", "Banking, tax, payments and finance back-office software."),
        "market_data_exchanges": ("Exchanges & Market Data", "Exchanges, ratings, indices and financial data."),
        "hr_legal_vertical": ("HR, Legal & Info Services", "HR/payroll, legal, tax and professional information."),
        "it_services_consulting": ("IT Services & Consulting", "Systems integrators and IT outsourcers."),
        "defense_gov": ("Defense & Government", "Government/defense applications and services, including civilian public-sector software."),
    }),
    "physical_ai": ("Physical AI & Industrial", {
        "robotics_automation": ("Robotics & Automation", "Industrial robots, machine vision and factory automation."),
        "autonomous_vehicles": ("Autonomous Vehicles", "ADAS, lidar/perception and autonomy-related vehicle systems; not unsupervised autonomy by itself."),
        "advanced_manufacturing": ("3D Printing & On-Demand Mfg", "Additive manufacturing and on-demand part production."),
        "industrial_components": ("Industrial Components & Flow", "Sensors, instrumentation, flow/fluid handling and engineered industrial components."),
    }),
}

# old sub -> new sub (1:1 or merge). Subs absent here and present in TAXONOMY keep their key.
MERGE = {
    "gpu_accelerators": "processors_accelerators",
    "custom_ai_accelerators": "processors_accelerators",
    "cpu_processor_ip": "processors_accelerators",
    "semicap_equipment": "semicap_materials",
    "semiconductor_materials": "semicap_materials",
    "test_measurement": "semicap_materials",
    "ems_distribution": "devices_ems_distribution",
    "client_devices": "devices_ems_distribution",
    "cloud_hyperscale": "cloud_platforms",
    "edge_cloud_services": "cloud_platforms",
    "datacenter_reit_edge": "datacenter_operators",
    "telecom_towers": "datacenter_operators",
    "energy_storage": "power_equipment",
    "power_generation_equipment": "power_equipment",
    "nuclear_fuel": "nuclear",
    "nuclear_reactors_services": "nuclear",
    "gas_midstream": "natural_gas",
    "gas_production": "natural_gas",
    "ai_platform_pureplay": "data_ai_platforms",
    "data_platforms": "data_ai_platforms",
    "business_intelligence": "data_ai_platforms",
    "infrastructure_software": "data_ai_platforms",
    "data_observability": "devtools_observability",
    "devtools_automation": "devtools_observability",
    "connected_operations": "enterprise_saas",
    "quantum": "quantum_computing",
    "fluid_handling": "industrial_components",
    "additive_manufacturing": "advanced_manufacturing",
    "on_demand_manufacturing": "advanced_manufacturing",
}

# old sub that splits in two: ticker decides, `default` for anyone not listed.
SPLIT = {
    "semis_broad": ("edge_rf_semis", {"analog_power_semis": {
        "STM", "DIOD", "POWI", "MPWR", "ALGM", "WOLF", "NVTS", "IFNNY", "AOSL", "6723.T", "6963.T",
        "TXN", "ON", "MCHP", "ADI", "NXPI"}}),
    "consumer_internet_media": ("social_media_streaming", {"consumer_commerce_mobility": {
        "DIDIY", "UBER", "LYFT", "GRAB", "JD", "PDD", "ZG", "TRIP", "ANGI", "YELP", "SE", "AMZN", "BABA"}}),
    "fintech_markets": ("payments_lending", {
        "market_data_exchanges": {"COIN", "MKTX", "ICE", "NDAQ", "MCO", "SPGI", "MSCI", "VRSK", "FDS", "MORN"},
        "fintech_software": {"INTU", "FIS", "FISV", "JKHY", "SSNC", "BILL", "QTWO", "NCNO"}}),
}


def remap_sub(sub: str, ticker: str) -> str:
    if sub in SPLIT:
        default, routes = SPLIT[sub]
        return next((new for new, tickers in routes.items() if ticker in tickers), default)
    return MERGE.get(sub, sub)


def remap_subs(subs: dict[str, float], ticker: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for sub, w in subs.items():
        new = remap_sub(sub, ticker)
        out[new] = round(out.get(new, 0) + w, 6)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def plain() -> dict[str, list[str]]:
    return {p: list(subs) for p, (_, subs) in TAXONOMY.items()}


def labels() -> dict[str, str]:
    out = {p: label for p, (label, _) in TAXONOMY.items()}
    for _, subs in TAXONOMY.values():
        out.update({s: lab for s, (lab, _) in subs.items()})
    return out


def descriptions() -> dict[str, str]:
    return {s: d for _, subs in TAXONOMY.values() for s, (_, d) in subs.items()}


def migrate_json(path: Path) -> int:
    data = json.loads(path.read_text())
    meta = data["_meta"]
    meta["taxonomy"] = plain()
    meta["taxonomy_labels"] = labels()
    meta["taxonomy_extensions"] = {}
    meta["taxonomy_scope_clarifications"] = descriptions()
    for s in data["stocks"]:
        s["subs"] = remap_subs(s.get("subs") or {}, s["ticker"])
        s["primary"] = _primary(s["subs"])
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return len(data["stocks"])


def _primary(subs: dict[str, float]) -> dict[str, float]:
    parent = {s: p for p, ss in plain().items() for s in ss}
    out: dict[str, float] = {}
    for s, w in subs.items():
        out[parent[s]] = round(out.get(parent[s], 0) + w, 6)
    return out


def migrate_db() -> int:
    from core import db

    con = db._conn()
    try:
        db._ensure_universe_tables(con)
        rows = con.execute("SELECT ticker, category, weight FROM ai_universe_category WHERE level='sub'").fetchall()
        by: dict[str, dict[str, float]] = {}
        for t, c, w in rows:
            by.setdefault(t, {})[c] = w
        con.execute("BEGIN")
        con.execute("DELETE FROM ai_universe_category")
        con.execute("DELETE FROM ai_taxonomy")
        db._insert_taxonomy(con, plain(), labels(), descriptions())
        for t, subs in by.items():
            subs = remap_subs(subs, t)
            prim = _primary(subs)
            con.executemany(
                "INSERT INTO ai_universe_category VALUES (?,?,?,?)",
                [[t, "primary", c, w] for c, w in prim.items()] + [[t, "sub", c, w] for c, w in subs.items()],
            )
            con.execute("UPDATE ai_universe SET primary_category=? WHERE ticker=?", [db._dominant(prim), t])
        con.execute("COMMIT")
        return len(by)
    finally:
        con.close()


if __name__ == "__main__":
    from core import db

    root = Path(db.UNIVERSE_JSON)
    print("db stocks:", migrate_db())
    print("json stocks:", migrate_json(root))
