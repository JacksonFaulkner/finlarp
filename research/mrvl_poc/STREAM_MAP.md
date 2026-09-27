# MRVL revenue stream map (2026-09-27)

Three layers per stream: **revenue** (reported vs mgmt-stated vs derived), **products + specs**, **patent activity**.
Labels: **[R]** reported in SEC filing · **[M]** stated by management on earnings call · **[D]** derived by us from [R]/[M] · **[3P]** third-party.

Next catalyst: **Investor Day 2026-10-06**. Likely finer split of Data Center; update this doc after.

## 1. Reported revenue

| Period          | Total     | Data center | Comms & other                     | DC % |
| --------------- | --------- | ----------- | --------------------------------- | ---- |
| FY25 (Feb-2025) | 5,767     | 4,164       | 1,603                             | 72%  |
| FY26 (Jan-2026) | 8,195     | 6,100       | 2,094                             | 74%  |
| Q1 FY26         | 1,895     | 1,441       | 455                               | 76%  |
| Q2 FY26         | 2,006     | 1,491       | 516                               | 74%  |
| Q3 FY26         | 2,075     | 1,518       | 557                               | 73%  |
| Q4 FY26         | 2,219     | 1,651       | 567                               | 74%  |
| Q1 FY27         | 2,418     | 1,833       | 585                               | 76%  |
| Q2 FY27         | 2,739     | 2,172       | 568                               | 79%  |
| Q3 FY27 guide   | 3,150 ±5% | —           | "down low-to-mid teens % QoQ" [M] | —    |

$M, [R] from 8-K EX-99.1 / 10-K. DC quarters sum to FY26 XBRL (6,100.3) exactly.
Before Q4 FY26 they reported 5 end markets. Last split (Q3 FY26): enterprise networking 237, carrier 168, consumer 117, auto/industrial 35.
Automotive ethernet sold to Infineon for $2.5B on 2025-08-14, so C&O before Q3 FY26 includes auto that's now gone.

**Outlook [M]:** FY27 $12B (+~45%), data center +60%. FY28 $18B (+~50%), data center >+60%.

## 2. Data center, broken down (no official split, so this is the estimate layer)

| Stream                                                      | FY26             | FY27                   | FY28                                | Basis                                   |
| ----------------------------------------------------------- | ---------------- | ---------------------- | ----------------------------------- | --------------------------------------- |
| Custom XPU + XPU-attach                                     | ~1,500 [M]       | >1,800 [D] (+20%+ [M]) | >3,600 [D] ("more than double" [M]) | FY29 target "$10B plus" [M]             |
| Interconnect (PAM4 DSP, TIA/driver, AEC, retimer, DCI, CPO) | ~3,500–4,000 [D] | +70% [M]               | —                                   | residual (see note)                     |
| of which DCI modules                                        | ~500 [D]         | —                      | ~1,000 annualized [M]               | "double FY26 levels"                    |
| of which scale-up optics (CPO/NPO, Celestial)               | ~0               | small                  | >300 [M], raised again in Q2        | prior outlook $150M, "more than double" |
| of which AEC + retimers                                     | —                | ">2x" [M]              | —                                   |                                         |
| Scale-out switching (Teralynx)                              | ~300 [D]         | >600 [M]               | >1,000 annualized [M]               | "more than double this year"            |
| Storage controllers, CXL, NIC, HSM                          | ~300–800 [D]     | —                      | —                                   | residual                                |
| **Data center total**                                       | **6,100 [R]**    | **~9,760 [D]**         | **>15,600 [D]**                     | +60% / >+60% [M]                        |

Residual: 6,100 − 1,500 custom − 300 switch = ~4,300 for interconnect + storage + other. Interconnect is the bulk (mgmt calls it the lead driver), but the split is not disclosed. Treat the range as a guess.

**Google deal [R]** (8-K 1.01, 2026-08-19): warrant for 58,970,907 shares @ $206.58. 240 tranches, each vests per **$500M of Custom Products revenue** from Google through FY2033, which works out to **$120B** of custom revenue at full vest. Products: inference accelerators, storage controllers, NICs, memory interface controllers, near-memory compute (TPU ecosystem). Expires 2033-08-18.

## 3. Products + specs by stream

### Custom XPU + XPU-attach (~18% of FY26 revenue)

- Programs [3P]: AWS Trainium 2 (production), Trainium follow-ons; Microsoft Maia; Google TPU-attach (8-K above). 18 XPU + XPU-attach sockets won; pipeline >50 opportunities (~$75B) [3P, from mgmt events].
- Platform [R 10-K]: 5nm shipped, 3nm in progress, 2nm/1.4nm (GAA, backside power) in development. IP: 200G+ SerDes, Arm compute, die-to-die, custom HBM, CPO, CoWoS/InFO/EMIB packaging.

### Interconnect (largest stream, est. ~45–50% of FY26 revenue)

| Product                                               | Spec                                                                                                                                                                         |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ara** 1.6T PAM4 optical DSP                         | TSMC 3nm; 8×200G host + 8×200G optical; <22W module (>20% lower than prior gen)                                                                                              |
| **Alaska A** 1.6T AEC DSP                             | 5nm; 8×200G host + 8×200G cable; >3m copper reach                                                                                                                            |
| **Alaska P** PCIe retimer                             | PCIe Gen6 / CXL; for AI server fabric, AEC/AOC                                                                                                                               |
| **COLORZ 800** ZR/ZR+ (DCI)                           | 800G at 1000km, 600G at 2000km; Orion coherent DSP + SiPh; −30% power/bit. 1.6T ZR+ launched OFC 2026                                                                        |
| **Photonic Fabric** (Celestial AI, closed 2026-02-02) | Gen-1 chiplet 16 Tbps; ~2.4 pJ/bit; ~100ns NIC-to-NIC, <200ns chip-to-memory; module 7.2 Tbps. Deal $3.25B upfront + up to $2.25B earnout if cumulative revenue >$2B by FY29 |
| Polariton (plasmonic modulators)                      | >1 THz modulator bandwidth [M]                                                                                                                                               |

### Switching (~4% of FY26 revenue, doubling)

| Product                   | Spec                                                                |
| ------------------------- | ------------------------------------------------------------------- |
| **Teralynx 10**           | 51.2 Tbps, 5nm, 64×800GbE, ~500–600ns latency; volume since 2024-07 |
| **Teralynx T100**         | 102.4 Tbps, announced 2026-06; claims −25% power vs competitors     |
| **Prestera**              | 12 Gbps–12.8 Tbps; enterprise/carrier/industrial (sits in C&O)      |
| XConn (closed 2026-02-10) | PCIe/CXL switches, feeds scale-up                                   |

### Storage / CXL / other data center

| Product                        | Spec                                                                                            |
| ------------------------------ | ----------------------------------------------------------------------------------------------- |
| **Bravera SC6** SSD controller | PCIe Gen6, NVMe 2.2                                                                             |
| **Structera A** CXL            | 5nm, 16× Neoverse V2, 4× DDR5-6400, up to 4TB added DRAM; Structera X/A compression up to 3.64× |
| LiquidSecurity HSM             | FIPS 140-3 L3; inside Azure Key Vault / Managed HSM                                             |
| HDD controllers/preamps        | legacy; MAMR driver patents still filed 2025                                                    |

### Communications & other (~26% of FY26, shrinking share)

Enterprise campus switches (Prestera), Alaska PHYs, **OCTEON 10** DPUs (5nm, 8–36 Neoverse N2, ~60W, integrated 1T switch, inline crypto) for 5G RAN/carrier, consumer broadband/PC/printers, industrial ethernet. FY27 growth ~10% [M], Q3 FY27 guided down low-to-mid teens %.

## 4. Patent layer (USPTO ODP, 13,815 applications, `pull_patents.py` + `analyze_patents.py`)

Filings by stream, bucketed on first matching CPC code:

| Stream                                          | 2019      | 2025     | Trend                                                 |
| ----------------------------------------------- | --------- | -------- | ----------------------------------------------------- |
| Interconnect (optics + SerDes/DSP + analog)     | 147 (35%) | 56 (31%) | steady share; **optics 11% → 21%**                    |
| Custom/compute (compute/mem + packaging + test) | 77 (18%)  | 57 (32%) | **packaging 15 → 34, highest ever**                   |
| Switching                                       | 42 (10%)  | 18 (10%) | flat                                                  |
| Storage                                         | 35 (8%)   | 17 (10%) | flat                                                  |
| Comms & other (wireless, security, auto)        | 84 (20%)  | 10 (6%)  | wireless 76 → 5 (consumer WiFi exit), auto → 0 (sold) |
| Total                                           | 421       | 178      | 2024–25 undercounted by the 18-month publication lag  |

Total US filings fell from ~650/yr (2016) to ~290 (2022). Leaner company, and the patent spend now concentrates on data center.

**2025–26 filings tell you what's next:**

- _Scale-up optics / CPO:_ comb laser, MZM dense interconnects, glass optical interposer, electrical bridge with photonic channel (Celestial / "Sicily Merger Sub II").
- _Optical memory:_ "optically disaggregated HBM," "optical memory module + cache manager," "photonic memory fabrics." Memory-over-optics for XPUs, matching the Google near-memory compute scope.
- _Custom XPU packaging:_ 3D processing-chiplet + SRAM-chiplet stacking, HBM system, stacked substrates on rigid carriers, liquid-metal TIM lid, irregular die perimeter for more beachfront I/O, die-to-die repair.
- _Scale-out/scale-up networking:_ tunneling over scale-out network, switch proxy, VOQ assignment, multi-stage scheduler.
- _SerDes:_ FEC with probabilistic constellation shaping, CDR phase-interpolator error correction (next-gen 400G/lane class).

## Caveats

- Only data center/C&O totals are [R]. Everything inside data center is [M] or [D]. Mgmt numbers come from call transcripts (Motley Fool), not filings.
- Custom FY26 "$1.5B" is mgmt's round number ("reached $1.5 billion annually").
- CPC bucketing is coarse: first matching code wins, ~10% have no CPC, and SerDes vs optics overlap.
- ODP applicant/assignee search misses filings where Marvell isn't named at filing and hasn't recorded an assignment yet.

Sources: MRVL 10-K FY26, 8-K EX-99.1 Q3 FY26–Q2 FY27, 8-K 2026-08-19 (Google warrant); Q4 FY26 / Q1 FY27 / Q2 FY27 call transcripts (fool.com); marvell.com product briefs + press kits (Ara, Alaska A, Teralynx, COLORZ 800, Structera, OCTEON 10); Celestial AI deal PR + Hot Chips 2025; USPTO ODP.
