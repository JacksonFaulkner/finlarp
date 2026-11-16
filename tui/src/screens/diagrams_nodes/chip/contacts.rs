// CHIP tab, CONTACTS: the node's overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on the contact layer (tools/pbr3d/blender/chip_contacts.py): the
// tungsten plugs from source, drain and gate up to thin metal, the silicide under them, and the
// current squeezing down a narrow plug, shown on a detailed cut-away of one transistor that replaces
// the schematic after beat 0. Zoom-ins a-e and sections 1-10 are detailed cut-aways too
// (chip_contacts_detail.py).

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("Contacts: the plugs from each transistor up to the first metal", BEAT_MS)
        .note(
            "Contacts are the short vertical plugs between each transistor and the first wiring level, the middle of line. Their resistance sits in series with every transistor on the chip.",
            "The whole chip, with the contact layer lit cyan over the two transistors.",
        )
        .detail(
            "Contacts limit every device on the chip.",
            &["PRE-CLEAN, SILICIDE, LINER, W FILL, CMP, VIA0/M1 (page text, section 1)"],
        ),
    Beat::new("Three plugs per transistor: source, gate and drain", BEAT_MS)
        .note(
            "The camera moves into the NMOS transistor and the schematic gives way to a real cross-section. Tungsten plugs in Ti/TiN liners land on the source and drain, a third plug reaches the gate through its SiN cap, and M1 copper lines sit on top.",
            "Grey tungsten plugs in gold liners between the violet gates, the green source and drain below, brown M1 cut ends along the top.",
        )
        .detail(
            "Every transistor needs all three.",
            &["Plugs ~15-20 nm wide (page text, section 4)", "M1 at 30-40 nm pitch (page text, section 2)"],
        ),
    Beat::new("Silicide: the metal-silicon bridge under each source and drain plug", BEAT_MS)
        .note(
            "Where the plug meets the doped silicon, titanium has reacted with the silicon to form a silicide a few nm thick. Metal on silicon forms a Schottky barrier; the silicide and heavy doping (above 1e20 per cm3) keep it thin enough for electrons to tunnel through.",
            "The pale silicide strip between the grey plug and the green drain epi.",
        )
        .detail(
            "Its barrier height to silicon sets the contact resistance.",
            &[
                "NiSi 0.65-0.7 eV; TiSi2 0.58 eV (patents, source [4])",
                "Dopant above 1e20 /cm3 (page text, section 2)",
            ],
        ),
    Beat::new("Current squeezes down a small plug", BEAT_MS)
        .note(
            "Current from M1 drops through via0 into the plug, a column only about 15-20 nm wide, then into the drain. One calculation puts tungsten's electron mean free path at 19.1 nm, wider than the plug's core, so the walls scatter electrons and resistance rises.",
            "Cyan beads dropping from the M1 line through via0 and down the grey plug into the green drain.",
        )
        .detail(
            "Surface scattering and the liner both raise the plug's resistance.",
            &[
                "W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])",
                "Plugs ~15-20 nm wide (page text, section 4)",
            ],
        ),
    Beat::new("Silicide lowers the contact resistance", BEAT_MS)
        .note(
            "The contact resistance is rho_c, the specific contact resistivity, divided by the contact area, and rho_c falls steeply as the Schottky barrier drops. A good silicide on heavily doped epi lets current cross the metal-silicon junction easily.",
            "The silicide strips glowing amber under both plugs, with beads streaming fast across them into the epi.",
        )
        .detail(
            "A lower barrier and heavier doping cut rho_c.",
            &[
                "R = rho_c / A (page text, section 4)",
                "rho_c pFET ~3e-9, nFET ~1e-8 ohm-cm2 (older patent background)",
                "Dopant segregation: 0.7 -> 0.34 eV (source [4])",
            ],
        ),
    Beat::new("Back out to the whole chip", BEAT_MS)
        .note(
            "Back out to the whole chip. Every transistor connects to the wiring through plugs like these, so their resistance matters on every path.",
            "The whole chip, the contact layer lit again.",
        )
        .detail(
            "Contact RC erodes node-to-node gains.",
            &["Contact RC erodes node-to-node gains (page text, section 9)"],
        ),
];

// ---- zoom-ins a-e: three beats each, the scenes chip_contacts.py builds as zoom_a..zoom_e ----

const ZA_BEATS: &[Beat] = &[
    Beat::new("PRE-CLEAN and SILICIDE on the source and drain", BEAT_MS)
        .note(
            "A hole is etched through the oxide down to the drain epi, and a pre-clean strips the thin native oxide that grows on bare silicon. Titanium deposited in the hole reacts with the silicon when annealed and forms a thin TiSi silicide.",
            "Close on the drain: a dark native-oxide film on the green epi disappears, then the silicide strip forms and glows amber at the bottom of the open hole.",
        )
        .detail(
            "Any oxide left at the bottom would add resistance.",
            &["PRE-CLEAN, SILICIDE (page text, section 1)", "Silicide a few nm (page text, section 2)"],
        ),
    Beat::new("LINER/BARRIER and W FILL", BEAT_MS)
        .note(
            "A Ti/TiN liner a few nm thick coats the hole so the tungsten sticks and the fluorine in its precursor can't attack the silicon. Tungsten is then grown from WF6 and hydrogen until the hole is full.",
            "Gold liner walls appear in the hole, cyan beads (the WF6 precursor) fall into it, then the grey tungsten core fills it.",
        )
        .detail(
            "The liner takes width the tungsten can't use.",
            &["LINER/BARRIER: Ti/TiN by ALD or CVD; W FILL from WF6 and H2 (page text, section 1)"],
        ),
    Beat::new("CMP and VIA0 / M1: the first metal lands", BEAT_MS)
        .note(
            "CMP polishes the tungsten flat, stopping on the oxide. An SiN etch stop goes on, then via0 and the M1 copper lines land on the plugs, and the transistor is wired to the rest of the chip.",
            "The whole device: plug tops polished flat, then the pale etch stop, brown via0 and M1 above, and cyan beads running from the drain up the plug to M1.",
        )
        .detail(
            "From here up, the wiring is copper.",
            &["CMP stops on the ILD; VIA0 / M1 land on the plug (page text, section 1)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("TRENCH CONTACT (TS): one bar straps source and drain", BEAT_MS)
        .note(
            "Seen from above, a trench contact is a long tungsten bar running the full width of the transistor, strapping its whole source or drain in one piece. Older nodes etched one hole per plug.",
            "From above: two long grey bars in gold liners with cyan beads running along them, and the short gate plug between.",
        )
        .detail(
            "Trench contacts now use self-aligned etch stops.",
            &["TS: a long bar strapping the source/drain epi (page text, section 3)"],
        ),
    Beat::new("GATE CONTACT: a plug on the gate metal", BEAT_MS)
        .note(
            "The gate is reached by a separate plug that passes through the gate's SiN cap to land on the gate metal. Via0 and M1 connect it to the wiring above.",
            "Cyan beads running down from M1 through via0 and the gate plug into the violet gate metal.",
        )
        .detail(
            "The gate contact used to sit off the active area.",
            &["GATE CONTACT: a plug on the gate metal (page text, section 3)"],
        ),
    Beat::new("SELECTIVE W: bottom-up fill, no seam", BEAT_MS)
        .note(
            "Conventional CVD tungsten grows inward from the walls of a lined hole, so the two fronts meet in a seam. Selective tungsten grows only from the bottom up, needs less liner and leaves no seam.",
            "Left: a grey plug in a gold liner with a dark seam down the middle. Right: an empty hole filling with grey tungsten from the bottom as cyan beads fall in.",
        )
        .detail(
            "Applied's figure is a vendor claim.",
            &["Applied selective W: over 40% lower contact R vs conventional W (vendor claim, source [5])"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("SAC CAP: a cap that forgives misalignment", BEAT_MS)
        .note(
            "Each gate carries a self-aligned SiN cap, with SiN spacers on its sides. A contact that lands off target hits SiN, which the contact etch doesn't remove, instead of shorting to the gate metal.",
            "An amber shape marks a misaligned contact overlapping a spacer, with a green glow where the SiN stops it, beside a gate's pale cap.",
        )
        .detail(
            "The cap tolerates misalignment.",
            &["SAC CAP: a SiN cap on the gate (page text, section 3)"],
        ),
    Beat::new("COAG: contact over active gate", BEAT_MS)
        .note(
            "Because the cap protects the gate, the gate contact can land right over the active channel instead of off at the end of the gate. Intel introduced this at 10 nm.",
            "Cyan beads running down the gate plug into the gate, with the channel under it glowing cyan.",
        )
        .detail(
            "Intel was first with COAG at 10 nm.",
            &["COAG: contact over active gate (page text, section 3)", "Intel 10 nm COAG (wikichip, source [7])"],
        ),
    Beat::new("a smaller standard cell", BEAT_MS)
        .note(
            "Moving the gate contact over the channel frees the space it used to need beside the active area, so the whole cell can be shorter. Intel credited COAG with roughly a 10% cut in cell height at 10 nm.",
            "Two standard cells from above, each with an amber gate-contact marker: on the left near the rail, on the right over the gates in a cell about 10% shorter.",
        )
        .detail(
            "A secondary-source claim.",
            &["Intel 10 nm COAG: ~10% cell height cut (Intel claim, secondary; source [7])"],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("CONTACT RESISTANCE: rho_c / A", BEAT_MS)
        .note(
            "Contact resistance is the specific contact resistivity rho_c divided by the contact area. A square contact half as wide has a quarter of the area and about four times the resistance, unless rho_c falls too.",
            "A 20 nm and a 10 nm plug with beads crossing each, slower in the small one, and two red bars, the second four times taller.",
        )
        .detail(
            "Contact area falls with the square of the pitch.",
            &[
                "R = rho_c / A (page text, section 4)",
                "rho_c pFET ~3e-9, nFET ~1e-8 ohm-cm2 (older patent background)",
            ],
        ),
    Beat::new("LINER SQUEEZE", BEAT_MS)
        .note(
            "The Ti/TiN liner is a few nm thick whatever the hole size. In a 40 nm square hole a 3 nm liner leaves about 72% of the area as tungsten; in a 15 nm hole it leaves about 36%.",
            "Two plugs seen at an angle from above: a big one with a thin gold ring round a wide grey core, and a small one where the gold ring takes much of the hole.",
        )
        .detail(
            "TiN doesn't shrink, so plug body resistance rises.",
            &[
                "Liner and TiN take a few nm per side (page text, section 4)",
                "3 nm liner: 40 nm hole ~72% W, 15 nm hole ~36% W (geometry)",
            ],
        ),
    Beat::new("BARRIER TUNING: dopant segregation", BEAT_MS)
        .note(
            "Where silicide meets silicon, electrons must cross the Schottky barrier. Implanting dopants before silicidation so they pile up at the interface cut it from about 0.7 to 0.34 eV in one patent, so more current gets through.",
            "The red bar beside the device drops to about half its height; afterwards more cyan beads pour down the plug into the drain.",
        )
        .detail(
            "A lower barrier cuts rho_c.",
            &["N2+ pre-silicide implant: 0.7 -> 0.34 eV (patent summary, source [4])"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("tungsten: the old standard", BEAT_MS)
        .note(
            "Tungsten fills the plugs. One calculation gives it an electron mean free path of 19.1 nm, wider than the ~14 nm core of a plug like this, so electrons hit the walls and the metal acts more resistive than in bulk.",
            "Close on a plug: a glowing yellow bar (the 19.1 nm mean free path) wider than the grey core between the gold liner walls, and beads zigzagging down.",
        )
        .detail(
            "Surface scattering in a narrow plug pushes the industry to new fills.",
            &["W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])"],
        ),
    Beat::new("cobalt: Intel 10 nm (2017)", BEAT_MS)
        .note(
            "Intel moved its lowest local wiring to cobalt at 10 nm in 2017. Cobalt gets by with a thinner liner than tungsten and resists electromigration well, so more of the hole carries current.",
            "A grey tungsten plug with a thick gold liner and a seam, a lilac-grey cobalt plug with a thinner liner, and an empty hole; beads running down both plugs.",
        )
        .detail(
            "Intel's claims for cobalt are 2x lower via resistance and 5-10x electromigration.",
            &["Intel 10 nm cobalt (source [6])", "W ~5.6, Co ~6.2 uOhm-cm bulk (approximate)"],
        ),
    Beat::new("Co, Ru, Mo: the next fills", BEAT_MS)
        .note(
            "Molybdenum and ruthenium can go in with little or no barrier, so the whole hole is metal. Their bulk resistivity is no better than tungsten's, but in a hole this narrow the liner they save matters more.",
            "The third hole fills with gold-grey molybdenum right out to the oxide walls, with beads running down it.",
        )
        .detail(
            "Less barrier raises adhesion and diffusion risk.",
            &["Bulk: Mo ~5.3, Ru ~7.1 uOhm-cm (approximate)", "New metals need new tools and qualification (page text, section 9)"],
        ),
];

// ---- sections 1-10, in the page's order: 3 beats each except sections 4 and 5 ----
// The pictures are detailed cut-aways of one transistor's contacts (chip_contacts_detail.py).

const SEC1_BEATS: &[Beat] = &[
    Beat::new("the transistor before its contacts", BEAT_MS)
        .note(
            "Contacts are the vertical plugs that connect each transistor to the first wiring level, the middle of line. Before they are made, the transistor's raised source and drain and its metal gates sit buried in oxide.",
            "A cut through three metal gates (dark violet, edged in yellow high-k, with pale SiN caps and teal spacers), green n+ source and drain blocks between them, all under sand-coloured oxide.",
        )
        .detail(
            "Contacts sit between the transistor and the wiring, in series with every device.",
            &["Contacts are the middle of line (page text, section 1)", "Gate pitch drawn ~60 nm (illustrative)"],
        ),
    Beat::new("the contact module, step by step", BEAT_MS)
        .note(
            "A hole is etched through the oxide down to the source or drain and the native oxide is cleaned off. Titanium reacts with the silicon to form a thin silicide, a Ti/TiN liner coats the hole, and tungsten made from WF6 and hydrogen fills it.",
            "Close on the drain: the hole opens, a pale silicide strip appears at its floor, gold liner walls appear, then a grey tungsten core fills the hole.",
        )
        .detail(
            "Each layer solves one problem: silicide for the barrier to silicon, liner for adhesion, tungsten for fill.",
            &[
                "PRE-CLEAN, SILICIDE, LINER/BARRIER, W FILL (page text, section 1)",
                "Ti/TiN liner a few nm (page text, section 1)",
            ],
        ),
    Beat::new("CMP, via0 and M1", BEAT_MS)
        .note(
            "CMP polishes the tungsten flat, stopping on the oxide. An SiN etch stop goes on top, then via0 and the first copper lines (M1) land on the plugs. Every transistor's current now passes through these plugs.",
            "The full stack: grey tungsten plugs under a thin pale etch stop, with brown copper vias and M1 lines above.",
        )
        .detail(
            "The plug is now the only path from the transistor to the wiring.",
            &["CMP stops on the ILD (page text, section 1)", "VIA0 / M1 land on the plug (page text, section 1)"],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("M1 and via0", BEAT_MS)
        .note(
            "At the top, M1 copper lines run into the picture at about a 30-40 nm pitch. A via0 drops from an M1 line through the SiN etch stop onto the tungsten plug below.",
            "Brown M1 cut ends with blue skins along the top, brown via0 columns under them, and the thin pale etch stop.",
        )
        .detail(
            "This is the first wiring over the transistors.",
            &["M1 at 30-40 nm pitch; via0 lands on a plug (page text, section 2)"],
        ),
    Beat::new("plugs, caps and spacers", BEAT_MS)
        .note(
            "The trench contact is a tungsten core inside a Ti/TiN liner, squeezed between two gates. The SiN cap on each gate and the spacers on its sides keep the contact from shorting to the gate, even if it is slightly misplaced.",
            "A grey tungsten plug in a gold liner, next to a gate's teal spacer and pale SiN cap.",
        )
        .detail(
            "The self-aligned cap lets the contact land close to the gate without shorting.",
            &["SiN cap on the gate, self-aligned (page text, section 2)", "Plugs ~15-20 nm wide (page text, section 4)"],
        ),
    Beat::new("silicide on the doped epi", BEAT_MS)
        .note(
            "At the bottom, the plug lands on a few nanometres of silicide (TiSi or NiSi) on the source/drain epi, which is doped above 1e20 atoms per cm3. Heavy doping thins the Schottky barrier between metal and silicon so electrons can tunnel through it.",
            "The pale silicide strip on the green epi at the foot of the plug, the dark silicon below and the channel under the next gate.",
        )
        .detail(
            "The silicide's barrier height to silicon sets the contact resistance.",
            &[
                "Silicide a few nm, dopant above 1e20 /cm3 (page text, section 2)",
                "NiSi 0.65-0.7 eV; TiSi2 0.58 eV (patents, source [4])",
            ],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("trench contacts and gate contacts", BEAT_MS)
        .note(
            "Seen from above, a trench contact (TS) is a long bar strapping the whole source or drain, and a gate contact is a single plug through the gate's cap. Older nodes etched one hole per plug.",
            "From above: two long grey tungsten bars in gold liners running back through the oxide, and one short plug on the middle gate.",
        )
        .detail(
            "Trench contacts now use self-aligned etch stops.",
            &["TS: a long bar on the S/D epi; GATE CONTACT: a plug on the gate metal (page text, section 3)"],
        ),
    Beat::new("SAC cap and COAG", BEAT_MS)
        .note(
            "The SiN cap and spacers act as a self-aligned etch stop: a contact that lands off target hits SiN, not gate metal. That margin also lets the gate contact sit right over the active channel (contact over active gate, COAG) instead of off to the side, which saves cell area.",
            "An amber shape marks a misaligned contact overlapping a spacer, with a green glow where the SiN stops it; the gate contact plug sits on the middle gate.",
        )
        .detail(
            "Intel first used COAG at 10 nm.",
            &[
                "COAG and SAC cap (page text, section 3)",
                "Intel 10 nm COAG: ~10% cell height cut (Intel claim, secondary; source [7])",
            ],
        ),
    Beat::new("selective tungsten: bottom-up, no seam", BEAT_MS)
        .note(
            "Conventional CVD tungsten grows inward from the walls of a lined hole, so the two fronts meet in a seam. Selective tungsten grows only from the bottom up, needs less liner and leaves no seam.",
            "Left: a grey plug in a gold liner with a dark seam down the middle. Right: an empty hole filling with grey tungsten from the bottom.",
        )
        .detail(
            "Applied's figure is a vendor claim.",
            &["Applied selective W: over 40% lower contact R vs conventional W (vendor claim, source [5])"],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("contact resistance sits in series", BEAT_MS)
        .note(
            "Current from M1 goes down a via and a plug, across the silicide into the drain, through the channel under the gate and back up the source side. Every one of those resistances adds, and as transistors shrink the contact pieces become a growing share.",
            "Cyan dots running from M1 down the right plug, through the green drain, under the middle gate and up the left plug, with tags on wire, plug, contact and channel.",
        )
        .detail(
            "Contact resistance adds to every device.",
            &["Total R = channel + S/D epi + contact + local wire (page text, section 4)"],
        ),
    Beat::new("a plug narrower than the electron's path", BEAT_MS)
        .note(
            "The tungsten core here is only about 14 nm wide. One calculation puts tungsten's electron mean free path at 19.1 nm, longer than the core is wide, so electrons hit the walls more often than anything else and the metal behaves as more resistive than in bulk.",
            "Close on one plug: a glowing yellow bar (the 19.1 nm mean free path) wider than the grey core between the gold liner walls, and dots zigzagging down the core.",
        )
        .detail(
            "Surface scattering, not bulk resistivity, decides a narrow plug's resistance.",
            &["W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])", "Plugs ~15-20 nm wide (page text, section 4)"],
        ),
    Beat::new("the liner squeeze", BEAT_MS)
        .note(
            "The Ti/TiN liner is a few nm thick whatever the hole size. In a 40 nm square hole a 3 nm liner leaves about 72% of the area as tungsten; in a 15 nm hole it leaves about 36%. The plug's resistance climbs far faster than its size falls.",
            "Two plugs seen at an angle from above: a big one with a thin gold ring round a wide grey core, and a small one where the gold ring takes much of the hole.",
        )
        .detail(
            "TiN doesn't shrink, so plug body resistance rises.",
            &[
                "Liner and TiN take a few nm per side (page text, section 4)",
                "3 nm liner: 40 nm hole ~72% W, 15 nm hole ~36% W (geometry)",
            ],
        ),
    Beat::new("lowering the Schottky barrier", BEAT_MS)
        .note(
            "Where silicide meets silicon there is an energy barrier, the Schottky barrier, that electrons must cross. Implanting dopants before silicidation so they pile up at the interface (dopant segregation) cut it from about 0.7 to 0.34 eV in one patent, so more current gets through.",
            "The red bar beside the device drops to about half its height; afterwards more cyan dots pour down the plug into the drain.",
        )
        .detail(
            "A lower barrier cuts rho_c, the contact resistance per unit area.",
            &["N2+ pre-silicide implant: 0.7 -> 0.34 eV (patent summary, source [4])"],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("W mean free path: 19.1 nm", BEAT_MS)
        .note(
            "One DFT calculation gives tungsten an electron mean free path of 19.1 nm at room temperature. A plug with a 14 nm core is narrower than that, which is why thin-film resistivity, not bulk resistivity, decides which metal wins.",
            "The glowing yellow 19.1 nm bar across the plug, wider than the grey core, with dots zigzagging down.",
        )
        .detail(
            "Surface scattering in a narrow plug is what makes this number matter.",
            &["W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])"],
        ),
    Beat::new("Schottky barrier heights", BEAT_MS)
        .note(
            "The barrier between silicide and n-type silicon is about 0.65-0.7 eV for NiSi and 0.58 eV for TiSi2, and dopant segregation can bring it to about 0.34 eV. A lower barrier gives a lower specific contact resistivity, rho_c.",
            "Three red bars on dark plinths: NiSi tallest, TiSi2 a little lower, the segregated one about half height.",
        )
        .detail(
            "Barrier height and doping together set rho_c.",
            &[
                "NiSi 0.65-0.7 eV; TiSi2 0.58 eV; segregated 0.34 eV (source [4])",
                "rho_c pFET ~3e-9, nFET ~1e-8 ohm-cm2 (older patent background)",
            ],
        ),
    Beat::new("bulk resistivity of the candidates", BEAT_MS)
        .note(
            "In bulk, copper conducts far better than the rest, but it needs a thick barrier and its lead fades in thin films. Tungsten, molybdenum, cobalt and ruthenium are three to four times worse in bulk; they win in contacts because they need less liner and lose less to thin-film scattering.",
            "Five bars in each metal's colour: a short copper bar, then molybdenum, tungsten, cobalt and a tall teal ruthenium bar.",
        )
        .detail(
            "Bulk values are approximate and are not what a narrow plug sees.",
            &["Cu ~1.7, Mo ~5.3, W ~5.6, Co ~6.2, Ru ~7.1 uOhm-cm (approximate)"],
        ),
    Beat::new("vendor and fab claims", BEAT_MS)
        .note(
            "Applied Materials says its Volta W cuts contact resistance by up to 90%, depending on size. Intel's 10 nm (2017) moved its lowest local wiring to cobalt, claiming 5-10x better electromigration. TSMC reported up to 20% lower middle-of-line R+C on N2.",
            "The whole device with three tags: on a tungsten plug, on the gate contact and on an M1 line.",
        )
        .detail(
            "These are claims under different test conditions, not one comparison.",
            &[
                "Applied Volta W: up to 90% lower contact R, CD dependent (vendor claim, source [5])",
                "Intel 10 nm cobalt: 5-10x electromigration (source [6])",
                "TSMC N2: up to 20% MOL R+C cut (reported, source [9])",
            ],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("Applied Materials FY2025: $28.37B", BEAT_MS)
        .note(
            "Applied Materials is one of the main suppliers of the deposition tools used to build contacts. Its FY2025 revenue was $28.37B: Semiconductor Systems (the tools) $20.80B, about 73%; Applied Global Services about 23%; the rest about 4%.",
            "A stacked bar: blue Semiconductor Systems at the bottom, teal Services above, a thin grey slice on top.",
        )
        .detail(
            "Revenue from the company's FY2025 10-K.",
            &["Revenue $28.37B; Semiconductor Systems $20.80B (AMAT FY2025 10-K, source [1])"],
        ),
    Beat::new("where the tools go", BEAT_MS)
        .note(
            "Of the $20.80B Semiconductor Systems revenue, 67% came from foundry, logic and other customers, 26% from DRAM and 7% from NAND. Foundry and logic customers, who adopt new contact metals first, are the largest share.",
            "A second bar beside the first: blue foundry/logic, teal DRAM and a thin grey NAND slice.",
        )
        .detail(
            "The segment split shows where the contact tools sell.",
            &["67% foundry/logic/other, 26% DRAM, 7% NAND (AMAT FY2025 10-K, source [1])"],
        ),
    Beat::new("the contact steps Applied sells", BEAT_MS)
        .note(
            "Applied's Endura platform carries the PVD, CVD and ALD chambers that lay down the Ti/TiN liner and the tungsten fill, and Applied also sells selective tungsten and cobalt processes for the newest contacts.",
            "The device with tags on a gold liner, a grey tungsten core and the gate contact.",
        )
        .detail(
            "These are Applied's own descriptions of its tools.",
            &["Endura PVD/CVD/ALD, cobalt, selective W (source [1], [5])"],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("tungsten: the long-time standard", BEAT_MS)
        .note(
            "Tungsten has filled contacts for decades because CVD fills tall, narrow holes well. But it needs a Ti/TiN liner about 3 nm a side, and conventional fill leaves a seam down the middle, so in a 20 nm hole much of the width isn't tungsten.",
            "A grey tungsten plug in a gold liner with a dark seam down its middle; the two holes to its right are still empty.",
        )
        .detail(
            "Liner and seam both take conductor away.",
            &["W bulk ~5.6 uOhm-cm (approximate)", "Liner a few nm per side (page text, section 4)"],
        ),
    Beat::new("cobalt: Intel 10 nm, 2017", BEAT_MS)
        .note(
            "Intel moved its lowest local wiring to cobalt at 10 nm in 2017. Cobalt gets by with a thinner liner than tungsten and resists electromigration well, so more of the hole carries current.",
            "The middle plug fills: a lilac-grey cobalt core inside a thinner gold liner.",
        )
        .detail(
            "Intel's claims for cobalt are 2x lower via resistance and 5-10x electromigration.",
            &["Intel 10 nm cobalt (source [6])", "Co bulk ~6.2 uOhm-cm (approximate)"],
        ),
    Beat::new("molybdenum and ruthenium: barrierless", BEAT_MS)
        .note(
            "Molybdenum and ruthenium can go in with little or no barrier, so the whole hole is metal. Lam sells molybdenum fill for contacts and Applied an ALD molybdenum process. The catch, without a liner, is adhesion and diffusion.",
            "The third plug fills with gold-grey molybdenum right out to the oxide walls.",
        )
        .detail(
            "Less barrier saves width but raises adhesion and diffusion risk.",
            &[
                "Mo ~5.3, Ru ~7.1 uOhm-cm (approximate)",
                "Barrierless fill raises adhesion and diffusion risk (page text, section 7)",
            ],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("the tool makers", BEAT_MS)
        .note(
            "Applied Materials (Endura PVD, CVD and ALD; cobalt; selective tungsten) and Lam Research (ALTUS CVD and ALD tungsten and molybdenum) are the main suppliers of the liner and fill steps. Lam's FY2025 revenue was $18.44B.",
            "Close on a contact, with tags on the gold liner and the grey tungsten core.",
        )
        .detail(
            "Tool suppliers for the contact step.",
            &["AMAT Endura; Lam ALTUS (page text, section 8)", "Lam FY2025 $18.44B (source [2])"],
        ),
    Beat::new("TSMC and Intel design the scheme", BEAT_MS)
        .note(
            "The foundries decide the contact scheme: which silicide, which liner, which fill metal and whether to use COAG. Intel was first with both cobalt and COAG at 10 nm.",
            "Tags on the silicide under the drain plug and on the gate contact over the middle gate.",
        )
        .detail(
            "Foundry choices set what the tools have to deposit.",
            &["TSMC (TSM) and Intel (INTC) (page text, section 8)"],
        ),
    Beat::new("buyers and the RC extractors", BEAT_MS)
        .note(
            "Samsung, SK hynix and Micron buy the same tools for DRAM and NAND, and Tokyo Electron sells competing CVD and ALD tools. Synopsys and Cadence software extracts each contact's resistance and capacitance so designers can time the circuit.",
            "The whole device with cyan dots running the current path, tagged with the buyers, TEL and the EDA firms.",
        )
        .detail(
            "Buyers, a second tool seller and the software that models the result.",
            &["Samsung, SK hynix, Micron; TEL 8035.T; Synopsys, Cadence (page text, section 8)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("new metals need new tools", BEAT_MS)
        .note(
            "Switching the plugs to molybdenum or ruthenium means new deposition chambers, new etch and clean chemistry, and months of qualification before a fab will run it in volume.",
            "The device with gold-grey molybdenum plugs and no gold liner.",
        )
        .detail(
            "Adoption risk.",
            &["New metals (Mo, Ru) need new tools and qualification (page text, section 9)"],
        ),
    Beat::new("barrierless: adhesion and diffusion", BEAT_MS)
        .note(
            "Without a liner, the metal may not stick well to the oxide, leaving voids along the walls, and metal atoms can diffuse into the dielectric and weaken it. Both show up as reliability failures over time, not on day one.",
            "Close on a molybdenum plug: a dark void along its left wall and red dots in the oxide beside it.",
        )
        .detail(
            "A reliability risk.",
            &["Barrierless fill raises adhesion and diffusion risk (page text, section 9)"],
        ),
    Beat::new("contact R erodes each node's gain", BEAT_MS)
        .note(
            "Contact resistance is rho_c divided by contact area. Halve the width of a square contact and its area falls to a quarter, so its resistance rises about four times unless rho_c falls too. That is how contact RC eats into each new node's speed gain.",
            "A 20 nm and a 10 nm plug seen from above, and two red bars: the second four times taller.",
        )
        .detail(
            "Contacts limit every device on the chip.",
            &[
                "R = rho_c / A (page text, section 4)",
                "Half the width: ~4x R at fixed rho_c (geometry)",
                "Contact RC erodes node-to-node gains (page text, section 9)",
            ],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1-3: the 10-Ks and the mean free path", BEAT_MS)
        .note(
            "The Applied and Lam 10-K filings, and the paper that gives tungsten's mean free path.",
            "The transistor and its contacts in cut-away, turning slowly.",
        )
        .detail(
            "Each number on this page traces to one of these.",
            &[
                "[1] AMAT FY2025 10-K: sec.gov/Archives/edgar/data/6951/000162828025056742/amat-20251026.htm",
                "[2] Lam FY2025 10-K: sec.gov/Archives/edgar/data/707549/000070754925000075/lrcx-20250629.htm",
                "[3] W mean free path: doi.org/10.1103/PHYSREVB.86.045432",
            ],
        ),
    Beat::new("sources 4-6: patents, Applied Volta W, Intel cobalt", BEAT_MS)
        .note(
            "The silicide patent, the Applied Volta W page, and Intel's cobalt interconnect article.",
            "The transistor and its contacts in cut-away, turning slowly.",
        )
        .detail(
            "Patent figures and vendor claims are marked as such on the page.",
            &[
                "[4] Silicide/SBH patents: image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10546856",
                "[5] Applied Volta W: appliedmaterials.com/jp/ja/semiconductor/products/processes/cvd/endura-volta-w-cvd.html",
                "[6] Intel 10nm Co: fuse.wikichip.org/news/525/iedm-2017-isscc-2018-intels-10nm-switching-to-cobalt-interconnects/",
            ],
        ),
    Beat::new("sources 7-9: COAG, Applied blog, TSMC N2", BEAT_MS)
        .note(
            "The COAG pages, Applied's contact-scaling blog, and TSMC's N2 paper summary.",
            "The transistor and its contacts in cut-away, turning slowly.",
        )
        .detail(
            "Intel's COAG figure is a secondary source.",
            &[
                "[7] COAG: en.wikichip.org/wiki/COAG ; community.cadence.com/cadence_blogs_8/b/breakfast-bytes/posts/intel-10nm",
                "[8] Applied blog: appliedmaterials.com/us/en/newsroom/blogs/powering-the-next-era-of-contact-scaling-with-ald-molybdenum.html",
                "[9] TSMC N2 IEDM 2024: semiconductor-digest.com/?p=30341",
            ],
        ),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_a.glb"),
        ZA_BEATS,
    )
}
fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_b.glb"),
        ZB_BEATS,
    )
}
fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_c.glb"),
        ZC_BEATS,
    )
}
fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_d.glb"),
        ZD_BEATS,
    )
}
fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the contact module: silicide to M1",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "contact types: trench, gate, selective W",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "SAC cap and COAG",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "contact resistance",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "new metals: cobalt, ruthenium, molybdenum",
        build: zoom_e,
    },
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_contacts_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order.
const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1_BEATS),
    section!(2, SEC2_BEATS),
    section!(3, SEC3_BEATS),
    section!(4, SEC4_BEATS),
    section!(5, SEC5_BEATS),
    section!(6, SEC6_BEATS),
    section!(7, SEC7_BEATS),
    section!(8, SEC8_BEATS),
    section!(9, SEC9_BEATS),
    section!(10, SEC10_BEATS),
];

pub const NODE: Node = Node {
    page: "CONTACTS",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zoom_keys_and_beat_counts_match_the_blender_scenes() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        let counts: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 3, 3]);
        for z in ZOOMS {
            let s = (z.build)();
            super::super::super::blender::explained(s.as_ref(), &format!("zoom {}", z.key));
            super::super::super::blender::draws_every_beat(s.as_ref(), &format!("zoom {}", z.key));
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 4, 4, 3, 3, 3, 3, 3]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }
}
