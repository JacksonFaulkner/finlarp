// Visuals for DEVELOP, ETCH, IMPLANT and CLEAN (group C). Generated from
// researched card data; see diagrams_vis.rs for the template.

use super::diagrams_vis::{Spot, TO_EOL, Visual, spot};

pub fn lookup(page: &str, card: &str, section: &str) -> Option<Visual> {
    let (art, spots) = match (page, card, section) {
        (r#"DEVELOP"#, r#"PEB"#, r#"Acid does the cutting"#) => (ART_1, SPOTS_1),
        (r#"DEVELOP"#, r#"PEB"#, r#"Too short, too long"#) => (ART_2, SPOTS_2),
        (r#"DEVELOP"#, r#"PEB"#, r#"Faster baking"#) => (ART_3, SPOTS_3),
        (r#"DEVELOP"#, r#"DEVELOP"#, r#"Dissolving the exposed part"#) => (ART_4, SPOTS_4),
        (r#"DEVELOP"#, r#"DEVELOP"#, r#"Swelling and collapse"#) => (ART_5, SPOTS_5),
        (r#"DEVELOP"#, r#"DEVELOP"#, r#"On the track"#) => (ART_6, SPOTS_6),
        (r#"DEVELOP"#, r#"RINSE"#, r#"Why thin lines fall over"#) => (ART_7, SPOTS_7),
        (r#"DEVELOP"#, r#"RINSE"#, r#"Rinse chemistry fixes"#) => (ART_8, SPOTS_8),
        (r#"DEVELOP"#, r#"RINSE"#, r#"Aspect ratio at High-NA"#) => (ART_9, SPOTS_9),
        (r#"DEVELOP"#, r#"TO ETCH"#, r#"The resist is a stencil"#) => (ART_10, SPOTS_10),
        (r#"DEVELOP"#, r#"TO ETCH"#, r#"Defects feed back"#) => (ART_11, SPOTS_11),
        (r#"DEVELOP"#, r#"TO ETCH"#, r#"Pull-through"#) => (ART_12, SPOTS_12),
        (r#"DEVELOP"#, r#"COOL"#, r#"Stopping the reaction"#) => (ART_13, SPOTS_13),
        (r#"DEVELOP"#, r#"COOL"#, r#"Time adds blur"#) => (ART_14, SPOTS_14),
        (r#"DEVELOP"#, r#"COOL"#, r#"Uniformity and speed"#) => (ART_15, SPOTS_15),
        (r#"DEVELOP"#, r#"QUENCHER"#, r#"The brake on acid"#) => (ART_16, SPOTS_16),
        (r#"DEVELOP"#, r#"QUENCHER"#, r#"The CAR trade-off"#) => (ART_17, SPOTS_17),
        (r#"DEVELOP"#, r#"QUENCHER"#, r#"Metal-oxide contrast"#) => (ART_18, SPOTS_18),
        (r#"DEVELOP"#, r#"TMAH dissolves"#, r#"What TMAH is"#) => (ART_19, SPOTS_19),
        (r#"DEVELOP"#, r#"TMAH dissolves"#, r#"A small, conflicting market"#) => (ART_20, SPOTS_20),
        (r#"DEVELOP"#, r#"TMAH dissolves"#, r#"Who supplies it"#) => (ART_21, SPOTS_21),
        (r#"DEVELOP"#, r#"Gaussian blur"#, r#"The blur formula"#) => (ART_22, SPOTS_22),
        (r#"DEVELOP"#, r#"Gaussian blur"#, r#"Worked values"#) => (ART_23, SPOTS_23),
        (r#"DEVELOP"#, r#"Gaussian blur"#, r#"If baking were instant"#) => (ART_24, SPOTS_24),
        (r#"DEVELOP"#, r#"HOT PLATE"#, r#"The bake module"#) => (ART_25, SPOTS_25),
        (r#"DEVELOP"#, r#"HOT PLATE"#, r#"Who builds it"#) => (ART_26, SPOTS_26),
        (r#"DEVELOP"#, r#"HOT PLATE"#, r#"Pace of the scanner"#) => (ART_27, SPOTS_27),
        (r#"DEVELOP"#, r#"CHUCK"#, r#"Develop module hardware"#) => (ART_28, SPOTS_28),
        (r#"DEVELOP"#, r#"CHUCK"#, r#"Uniform dissolution"#) => (ART_29, SPOTS_29),
        (r#"DEVELOP"#, r#"CHUCK"#, r#"Pull-through for TEL"#) => (ART_30, SPOTS_30),
        (r#"DEVELOP"#, r#"Metal-oxide resists"#, r#"More photons, rougher edges"#) => {
            (ART_31, SPOTS_31)
        }
        (r#"DEVELOP"#, r#"Metal-oxide resists"#, r#"Stochastics at High-NA"#) => (ART_32, SPOTS_32),
        (r#"DEVELOP"#, r#"Metal-oxide resists"#, r#"Suppliers and the licence deal"#) => {
            (ART_33, SPOTS_33)
        }
        (r#"DEVELOP"#, r#"Lam DRY RESIST"#, r#"What dry resist is"#) => (ART_34, SPOTS_34),
        (r#"DEVELOP"#, r#"Lam DRY RESIST"#, r#"Claimed benefits"#) => (ART_35, SPOTS_35),
        (r#"DEVELOP"#, r#"Lam DRY RESIST"#, r#"Who gains, who loses"#) => (ART_36, SPOTS_36),
        (r#"DEVELOP"#, r#"Chokepoints"#, r#"Tracks and chemicals"#) => (ART_37, SPOTS_37),
        (r#"DEVELOP"#, r#"Chokepoints"#, r#"Risks"#) => (ART_38, SPOTS_38),
        (r#"DEVELOP"#, r#"Chokepoints"#, r#"One cluster"#) => (ART_39, SPOTS_39),
        (r#"ETCH"#, r#"HARD MASK"#, r#"Resist is too soft"#) => (ART_40, SPOTS_40),
        (r#"ETCH"#, r#"HARD MASK"#, r#"Selectivity caps depth"#) => (ART_41, SPOTS_41),
        (r#"ETCH"#, r#"HARD MASK"#, r#"Layers drive etch demand"#) => (ART_42, SPOTS_42),
        (r#"ETCH"#, r#"IGNITE"#, r#"From neutral gas to plasma"#) => (ART_43, SPOTS_43),
        (r#"ETCH"#, r#"IGNITE"#, r#"RIE versus ICP"#) => (ART_44, SPOTS_44),
        (r#"ETCH"#, r#"IGNITE"#, r#"Drift and chamber matching"#) => (ART_45, SPOTS_45),
        (r#"ETCH"#, r#"RADICALS"#, r#"The chemical half"#) => (ART_46, SPOTS_46),
        (r#"ETCH"#, r#"RADICALS"#, r#"Gas choices by film"#) => (ART_47, SPOTS_47),
        (r#"ETCH"#, r#"RADICALS"#, r#"When radicals are the point"#) => (ART_48, SPOTS_48),
        (r#"ETCH"#, r#"ION-ASSISTED"#, r#"Ions make it vertical"#) => (ART_49, SPOTS_49),
        (r#"ETCH"#, r#"ION-ASSISTED"#, r#"Source power and bias"#) => (ART_50, SPOTS_50),
        (r#"ETCH"#, r#"ION-ASSISTED"#, r#"Deep holes starve for ions"#) => (ART_51, SPOTS_51),
        (r#"ETCH"#, r#"SIDEWALL"#, r#"The protective film"#) => (ART_52, SPOTS_52),
        (r#"ETCH"#, r#"SIDEWALL"#, r#"A balancing act"#) => (ART_53, SPOTS_53),
        (r#"ETCH"#, r#"SIDEWALL"#, r#"Cryo changes the balance"#) => (ART_54, SPOTS_54),
        (r#"ETCH"#, r#"STRIP"#, r#"Remove the helpers"#) => (ART_55, SPOTS_55),
        (r#"ETCH"#, r#"STRIP"#, r#"Why etch and clean are bundled"#) => (ART_56, SPOTS_56),
        (r#"ETCH"#, r#"STRIP"#, r#"Yield risks in strip"#) => (ART_57, SPOTS_57),
        (r#"ETCH"#, r#"SHOWERHEAD"#, r#"Even gas delivery"#) => (ART_58, SPOTS_58),
        (r#"ETCH"#, r#"SHOWERHEAD"#, r#"A consumable part"#) => (ART_59, SPOTS_59),
        (r#"ETCH"#, r#"SHOWERHEAD"#, r#"Chamber design differentiates"#) => (ART_60, SPOTS_60),
        (r#"ETCH"#, r#"PLASMA:"#, r#"Three species"#) => (ART_61, SPOTS_61),
        (r#"ETCH"#, r#"PLASMA:"#, r#"The sheath"#) => (ART_62, SPOTS_62),
        (r#"ETCH"#, r#"PLASMA:"#, r#"Why ICP replaced RIE"#) => (ART_63, SPOTS_63),
        (r#"ETCH"#, r#"ESC"#, r#"Holding and cooling the wafer"#) => (ART_64, SPOTS_64),
        (r#"ETCH"#, r#"ESC"#, r#"Cryo etch demands more"#) => (ART_65, SPOTS_65),
        (r#"ETCH"#, r#"ESC"#, r#"Failure modes"#) => (ART_66, SPOTS_66),
        (r#"ETCH"#, r#"cathode"#, r#"The bottom electrode"#) => (ART_67, SPOTS_67),
        (r#"ETCH"#, r#"cathode"#, r#"Bias is the deep-hole lever"#) => (ART_68, SPOTS_68),
        (r#"ETCH"#, r#"cathode"#, r#"Pull from NAND and HBM"#) => (ART_69, SPOTS_69),
        (r#"ETCH"#, r#"Lam Cryo 3.0"#, r#"What it is"#) => (ART_70, SPOTS_70),
        (r#"ETCH"#, r#"Lam Cryo 3.0"#, r#"Why NAND needs it"#) => (ART_71, SPOTS_71),
        (r#"ETCH"#, r#"Lam Cryo 3.0"#, r#"Risk"#) => (ART_72, SPOTS_72),
        (r#"ETCH"#, r#"NAND channel hole"#, r#"A very deep, very thin hole"#) => (ART_73, SPOTS_73),
        (r#"ETCH"#, r#"NAND channel hole"#, r#"How holes fail"#) => (ART_74, SPOTS_74),
        (r#"ETCH"#, r#"NAND channel hole"#, r#"Why AI cares"#) => (ART_75, SPOTS_75),
        (r#"ETCH"#, r#"aspect ratio"#, r#"Depth over width"#) => (ART_76, SPOTS_76),
        (r#"ETCH"#, r#"aspect ratio"#, r#"Why depth is hard"#) => (ART_77, SPOTS_77),
        (r#"ETCH"#, r#"aspect ratio"#, r#"Industry responses"#) => (ART_78, SPOTS_78),
        (r#"ETCH"#, r#"ALE"#, r#"Two self-limiting steps"#) => (ART_79, SPOTS_79),
        (r#"ETCH"#, r#"ALE"#, r#"Numbers from simulation"#) => (ART_80, SPOTS_80),
        (r#"ETCH"#, r#"ALE"#, r#"Where it is used"#) => (ART_81, SPOTS_81),
        (r#"ETCH"#, r#"China"#, r#"Lam's biggest region"#) => (ART_82, SPOTS_82),
        (r#"ETCH"#, r#"China"#, r#"Who is buying"#) => (ART_83, SPOTS_83),
        (r#"ETCH"#, r#"China"#, r#"Open questions"#) => (ART_84, SPOTS_84),
        (r#"ETCH"#, r#"Etch+clean 22"#, r#"Share of wafer-fab equipment"#) => (ART_85, SPOTS_85),
        (r#"ETCH"#, r#"Etch+clean 22"#, r#"Why it swings"#) => (ART_86, SPOTS_86),
        (r#"ETCH"#, r#"Etch+clean 22"#, r#"Investor read"#) => (ART_87, SPOTS_87),
        (r#"ETCH"#, r#"Tokyo Electron"#, r#"Number two in etch"#) => (ART_88, SPOTS_88),
        (r#"ETCH"#, r#"Tokyo Electron"#, r#"Estimated share"#) => (ART_89, SPOTS_89),
        (r#"ETCH"#, r#"Tokyo Electron"#, r#"Competitive map"#) => (ART_90, SPOTS_90),
        (r#"ETCH"#, r#"Lam Research (LRCX)"#, r#"The pure play"#) => (ART_91, SPOTS_91),
        (r#"ETCH"#, r#"Lam Research (LRCX)"#, r#"Product pillars"#) => (ART_92, SPOTS_92),
        (r#"ETCH"#, r#"Lam Research (LRCX)"#, r#"Risks"#) => (ART_93, SPOTS_93),
        (r#"IMPLANT"#, r#"SOURCE"#, r#"Making ions"#) => (ART_94, SPOTS_94),
        (r#"IMPLANT"#, r#"SOURCE"#, r#"Which gas for which dopant"#) => (ART_95, SPOTS_95),
        (r#"IMPLANT"#, r#"SOURCE"#, r#"Source sets throughput"#) => (ART_96, SPOTS_96),
        (r#"IMPLANT"#, r#"EXTRACT"#, r#"Pulling ions out"#) => (ART_97, SPOTS_97),
        (r#"IMPLANT"#, r#"EXTRACT"#, r#"Space charge limit"#) => (ART_98, SPOTS_98),
        (r#"IMPLANT"#, r#"EXTRACT"#, r#"Failure modes"#) => (ART_99, SPOTS_99),
        (r#"IMPLANT"#, r#"MASS"#, r#"Bending by mass"#) => (ART_100, SPOTS_100),
        (r#"IMPLANT"#, r#"MASS"#, r#"Many species leave the source"#) => (ART_101, SPOTS_101),
        (r#"IMPLANT"#, r#"MASS"#, r#"Why implant has no substitute"#) => (ART_102, SPOTS_102),
        (r#"IMPLANT"#, r#"ACCEL"#, r#"Energy sets depth"#) => (ART_103, SPOTS_103),
        (r#"IMPLANT"#, r#"ACCEL"#, r#"Energy ranges by class"#) => (ART_104, SPOTS_104),
        (r#"IMPLANT"#, r#"ACCEL"#, r#"Why Axcelis cares"#) => (ART_105, SPOTS_105),
        (r#"IMPLANT"#, r#"SCAN +"#, r#"Spreading the beam evenly"#) => (ART_106, SPOTS_106),
        (r#"IMPLANT"#, r#"SCAN +"#, r#"Dose is current times time"#) => (ART_107, SPOTS_107),
        (r#"IMPLANT"#, r#"SCAN +"#, r#"Tilt and shadowing"#) => (ART_108, SPOTS_108),
        (r#"IMPLANT"#, r#"ANNEAL"#, r#"Repair and activate"#) => (ART_109, SPOTS_109),
        (r#"IMPLANT"#, r#"ANNEAL"#, r#"Heat versus diffusion"#) => (ART_110, SPOTS_110),
        (r#"IMPLANT"#, r#"ANNEAL"#, r#"Thermal budget"#) => (ART_111, SPOTS_111),
        (r#"IMPLANT"#, r#"ANALYZER"#, r#"A single-species beam"#) => (ART_112, SPOTS_112),
        (r#"IMPLANT"#, r#"ANALYZER"#, r#"Resolution and vacuum"#) => (ART_113, SPOTS_113),
        (r#"IMPLANT"#, r#"ANALYZER"#, r#"Transmission and tool lineup"#) => (ART_114, SPOTS_114),
        (r#"IMPLANT"#, r#"Faraday cup"#, r#"Counting charge"#) => (ART_115, SPOTS_115),
        (r#"IMPLANT"#, r#"Faraday cup"#, r#"Dose is the spec"#) => (ART_116, SPOTS_116),
        (r#"IMPLANT"#, r#"Faraday cup"#, r#"Failure modes"#) => (ART_117, SPOTS_117),
        (r#"IMPLANT"#, r#"channeling"#, r#"Open corridors in silicon"#) => (ART_118, SPOTS_118),
        (r#"IMPLANT"#, r#"channeling"#, r#"Two fixes"#) => (ART_119, SPOTS_119),
        (r#"IMPLANT"#, r#"channeling"#, r#"The normal profile"#) => (ART_120, SPOTS_120),
        (r#"IMPLANT"#, r#"high current"#, r#"Heavy dose, low energy"#) => (ART_121, SPOTS_121),
        (r#"IMPLANT"#, r#"high current"#, r#"The scaling pain"#) => (ART_122, SPOTS_122),
        (r#"IMPLANT"#, r#"high current"#, r#"Three classes"#) => (ART_123, SPOTS_123),
        (r#"IMPLANT"#, r#"Applied Mat."#, r#"Market share"#) => (ART_124, SPOTS_124),
        (r#"IMPLANT"#, r#"Applied Mat."#, r#"Share over time"#) => (ART_125, SPOTS_125),
        (r#"IMPLANT"#, r#"Applied Mat."#, r#"Why it is not the stock driver"#) => {
            (ART_126, SPOTS_126)
        }
        (r#"IMPLANT"#, r#"Axcelis"#, r#"Almost pure implant"#) => (ART_127, SPOTS_127),
        (r#"IMPLANT"#, r#"Axcelis"#, r#"The Veeco merger"#) => (ART_128, SPOTS_128),
        (r#"IMPLANT"#, r#"Axcelis"#, r#"SiC position"#) => (ART_129, SPOTS_129),
        (r#"IMPLANT"#, r#"SEN (Sumitomo Heavy 6302.T)"#, r#"A 50/50 joint venture"#) => {
            (ART_130, SPOTS_130)
        }
        (r#"IMPLANT"#, r#"SEN (Sumitomo Heavy 6302.T)"#, r#"What is not confirmed"#) => {
            (ART_131, SPOTS_131)
        }
        (r#"IMPLANT"#, r#"SEN (Sumitomo Heavy 6302.T)"#, r#"Why Japan matters"#) => {
            (ART_132, SPOTS_132)
        }
        (r#"IMPLANT"#, r#"laser anneal"#, r#"Surface-only heating"#) => (ART_133, SPOTS_133),
        (r#"IMPLANT"#, r#"laser anneal"#, r#"Shorter and hotter"#) => (ART_134, SPOTS_134),
        (r#"IMPLANT"#, r#"laser anneal"#, r#"Failure modes"#) => (ART_135, SPOTS_135),
        (r#"CLEAN"#, r#"ORGANICS"#, r#"SPM: the hot first step"#) => (ART_136, SPOTS_136),
        (r#"CLEAN"#, r#"ORGANICS"#, r#"Side effects"#) => (ART_137, SPOTS_137),
        (r#"CLEAN"#, r#"ORGANICS"#, r#"Step counts rise with layers"#) => (ART_138, SPOTS_138),
        (r#"CLEAN"#, r#"RINSE"#, r#"DI water between every chemistry"#) => (ART_139, SPOTS_139),
        (r#"CLEAN"#, r#"RINSE"#, r#"Water quality"#) => (ART_140, SPOTS_140),
        (r#"CLEAN"#, r#"RINSE"#, r#"Rinse time costs throughput"#) => (ART_141, SPOTS_141),
        (r#"CLEAN"#, r#"OXIDE"#, r#"DHF: strip native oxide"#) => (ART_142, SPOTS_142),
        (r#"CLEAN"#, r#"OXIDE"#, r#"A clean but reactive surface"#) => (ART_143, SPOTS_143),
        (r#"CLEAN"#, r#"OXIDE"#, r#"Order and failure modes"#) => (ART_144, SPOTS_144),
        (r#"CLEAN"#, r#"PARTICLES"#, r#"SC1 undercuts particles"#) => (ART_145, SPOTS_145),
        (r#"CLEAN"#, r#"PARTICLES"#, r#"Charge repulsion"#) => (ART_146, SPOTS_146),
        (r#"CLEAN"#, r#"PARTICLES"#, r#"Roughness versus removal"#) => (ART_147, SPOTS_147),
        (r#"CLEAN"#, r#"METALS"#, r#"SC2 turns metals into chlorides"#) => (ART_148, SPOTS_148),
        (r#"CLEAN"#, r#"METALS"#, r#"The quiet killer"#) => (ART_149, SPOTS_149),
        (r#"CLEAN"#, r#"METALS"#, r#"Modern variants"#) => (ART_150, SPOTS_150),
        (r#"CLEAN"#, r#"DRY"#, r#"Water must leave cleanly"#) => (ART_151, SPOTS_151),
        (r#"CLEAN"#, r#"DRY"#, r#"Supercritical CO2"#) => (ART_152, SPOTS_152),
        (r#"CLEAN"#, r#"DRY"#, r#"Batch versus single-wafer drying"#) => (ART_153, SPOTS_153),
        (r#"CLEAN"#, r#"chem nozzle arm"#, r#"Dispensing onto a spinning wafer"#) => {
            (ART_154, SPOTS_154)
        }
        (r#"CLEAN"#, r#"chem nozzle arm"#, r#"Fresh chemistry each wafer"#) => (ART_155, SPOTS_155),
        (r#"CLEAN"#, r#"chem nozzle arm"#, r#"Vendors"#) => (ART_156, SPOTS_156),
        (r#"CLEAN"#, r#"megasonic transducer"#, r#"Sound that shears particles"#) => {
            (ART_157, SPOTS_157)
        }
        (r#"CLEAN"#, r#"megasonic transducer"#, r#"A narrow window"#) => (ART_158, SPOTS_158),
        (r#"CLEAN"#, r#"megasonic transducer"#, r#"Pressure points"#) => (ART_159, SPOTS_159),
        (r#"CLEAN"#, r#"splash guard"#, r#"Bowl, rings and drains"#) => (ART_160, SPOTS_160),
        (r#"CLEAN"#, r#"splash guard"#, r#"Hazardous chemistry"#) => (ART_161, SPOTS_161),
        (r#"CLEAN"#, r#"splash guard"#, r#"Cross-contamination"#) => (ART_162, SPOTS_162),
        (r#"CLEAN"#, r#"Marangoni"#, r#"The meniscus pulls lines together"#) => {
            (ART_163, SPOTS_163)
        }
        (r#"CLEAN"#, r#"Marangoni"#, r#"Methods compared"#) => (ART_164, SPOTS_164),
        (r#"CLEAN"#, r#"Marangoni"#, r#"Why scCO2 is not everywhere"#) => (ART_165, SPOTS_165),
        (r#"CLEAN"#, r#"BATCH WET BENCH"#, r#"Batch versus single-wafer"#) => (ART_166, SPOTS_166),
        (r#"CLEAN"#, r#"BATCH WET BENCH"#, r#"SCREEN's position"#) => (ART_167, SPOTS_167),
        (r#"CLEAN"#, r#"BATCH WET BENCH"#, r#"Drift to single-wafer"#) => (ART_168, SPOTS_168),
        (r#"CLEAN"#, r#"Etch + clean"#, r#"A slice of WFE"#) => (ART_169, SPOTS_169),
        (r#"CLEAN"#, r#"Etch + clean"#, r#"Who sells it"#) => (ART_170, SPOTS_170),
        (r#"CLEAN"#, r#"Etch + clean"#, r#"Why it grows with AI"#) => (ART_171, SPOTS_171),
        (r#"CLEAN"#, r#"SC1"#, r#"Recipe spread"#) => (ART_172, SPOTS_172),
        (r#"CLEAN"#, r#"SC1"#, r#"Self-limiting chemistry"#) => (ART_173, SPOTS_173),
        (r#"CLEAN"#, r#"SC1"#, r#"Failure modes"#) => (ART_174, SPOTS_174),
        (r#"CLEAN"#, r#"Report C 2023"#, r#"Why the market size is uncertain"#) => {
            (ART_175, SPOTS_175)
        }
        (r#"CLEAN"#, r#"Report C 2023"#, r#"Cross-checks"#) => (ART_176, SPOTS_176),
        (r#"CLEAN"#, r#"Report C 2023"#, r#"Better anchors"#) => (ART_177, SPOTS_177),
        _ => return None,
    };
    Some(Visual { art, spots })
}

const ART_1: &str = r#"# One acid, many cuts

     photoacid H+
          |
          v
  ┌───────────────┐  cut   ┌───────────────┐
  │ protecting    │───────▶│ polymer-COOH  │
  │ group on the  │        │ dissolves in  │
  │ polymer       │        │ TMAH later    │
  └───────────────┘        └───────────────┘
          |
          v
   H+ regenerated ──▶ goes on to cut the next group

  (catalytic: up to several hundred reactions per acid)
  (t-butyl ester shown; real resists mix protecting groups)
"#;
const SPOTS_1: &[Spot] = &[
    spot(
        r#"photoacid H+"#,
        0,
        0,
        r#"Acid made by the exposure. At this point the wafer holds only a latent chemical image, not a physical pattern."#,
    ),
    spot(
        r#"protecting"#,
        0,
        0,
        r#"Protecting groups, such as t-butyl ester, make the polymer insoluble in the aqueous developer."#,
    ),
    spot(
        r#"polymer-COOH"#,
        0,
        0,
        r#"Once the protecting group is cut off, the polymer carries a carboxylic acid group that dissolves in aqueous base."#,
    ),
    spot(
        r#"H+ regenerated"#,
        0,
        0,
        r#"The acid is not used up, so one photon's acid can cut many groups. That is the chemical amplification."#,
    ),
    spot(
        r#"(catalytic: up to several hundred reactions per acid)"#,
        0,
        0,
        r#"A patent on measuring catalyst diffusion says catalytic chain length can be very long, up to several hundred reaction events."#,
    ),
];

const ART_2: &str = r#"# The edge after the bake

        exposed             edge        unexposed
  ideal ░░░░░░░░░░░░░░░░░░░░░│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  short ░░░░░░░░░░░░░░░░░░▒▒▒│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  long  ░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓

  ░ deprotected (dissolves)  ▒ partly  ▓ protected (stays)

  short / cool: weak deprotection, needs more dose
  long / hot:   acid diffuses past the edge, line blurs
  (diffusion lengths reported from ~5 nm to tens of nm)
"#;
const SPOTS_2: &[Spot] = &[
    spot(
        r#"ideal"#,
        0,
        0,
        r#"The target: a sharp step between deprotected and protected polymer right at the edge of the exposed region."#,
    ),
    spot(
        r#"short"#,
        0,
        0,
        r#"Too short or too cool: deprotection is weak and incomplete, so more dose is needed to compensate."#,
    ),
    spot(
        r#"long "#,
        0,
        0,
        r#"Too long or too hot: acid diffuses across the edge, which blurs and roughens the line."#,
    ),
    spot(
        r#"(diffusion lengths reported from ~5 nm to tens of nm)"#,
        0,
        0,
        r#"Reported values vary by resist and measurement method: about 5 nm in older IBM work, about 8 nm in a calibrated EUV model, a few tens of nm in general overviews."#,
    ),
];

const ART_3: &str = r#"# Hot plate versus laser bake (research)

  acid diffusivity
    hot plate   ████████████████████████████████ 1x (reference)
    laser, ms   ▏ 100-1000x lower

  EUV dose needed
    hot plate   ████████████████████████████████ 100%
    laser, ms   ███████████████ under 50%

  (one ORNL-linked study; not a production process)
  (hot plate: 90-150 C for 30-120 s)
"#;
const SPOTS_3: &[Spot] = &[
    spot(
        r#"hot plate   ████"#,
        0,
        TO_EOL,
        r#"Reference case: seconds on a hot plate, long enough for acid to wander."#,
    ),
    spot(
        r#"laser, ms   ▏"#,
        0,
        TO_EOL,
        r#"The study reports acid diffusivity 100-1000x lower than hot-plate extrapolations when the bake lasts only milliseconds."#,
    ),
    spot(
        r#"laser, ms   ███"#,
        0,
        TO_EOL,
        r#"The same study reports under half the EUV dose, since less blur means less dose is needed to compensate."#,
    ),
    spot(
        r#"(one ORNL-linked study; not a production process)"#,
        0,
        0,
        r#"Treat as a research result. No production tool is cited."#,
    ),
];

const ART_4: &str = r#"# Develop: the soluble part washes away

  polymer-COOH + OH-  ──▶  polymer-COO- + H2O
  (deprotected)   (TMAH)   (carboxylate: dissolves)

  before develop            after develop
  ▓▓▓░░░▓▓▓░░░▓▓▓           ▓▓▓   ▓▓▓   ▓▓▓
  ═══════════════           ═══════════════
  ▓ protected, stays   ░ deprotected, dissolves

  (TMAH = (CH3)4N+ OH-, 2.38 wt%, about 0.26 mol/L)
"#;
const SPOTS_4: &[Spot] = &[
    spot(
        r#"polymer-COOH"#,
        0,
        0,
        r#"The deprotected polymer after the bake, carrying carboxylic acid groups."#,
    ),
    spot(
        r#"OH-"#,
        0,
        0,
        r#"Hydroxide from the aqueous TMAH developer takes a proton from the acid group."#,
    ),
    spot(
        r#"polymer-COO-"#,
        0,
        0,
        r#"The carboxylate form is soluble in the aqueous developer, so it washes off the wafer."#,
    ),
    spot(
        r#"before develop"#,
        0,
        0,
        r#"After exposure and PEB the film is still continuous: protected and deprotected regions side by side."#,
    ),
    spot(
        r#"after develop"#,
        0,
        0,
        r#"Only the protected polymer is left, as lines. This is the resist stencil that etch will copy."#,
    ),
    spot(
        r#"(TMAH = (CH3)4N+ OH-, 2.38 wt%, about 0.26 mol/L)"#,
        0,
        0,
        r#"2.38 wt% is the standard concentration. 23.8 g/L over a molar mass of 91.15 g/mol gives about 0.26 mol/L (computed)."#,
    ),
];

const ART_5: &str = r#"# Developer swells the lines

  dry            swollen          rinse + dry
  ▓▓   ▓▓   ▓▓   ▓▓▓▓ ▓▓▓▓ ▓▓▓▓   ▓▓▓▓▓▓▓▓   ▓▓▓▓
  ▓▓   ▓▓   ▓▓   ▓▓▓▓ ▓▓▓▓ ▓▓▓▓   ▓▓▓▓▓▓▓▓   ▓▓▓▓
  ▓▓   ▓▓   ▓▓   ▓▓▓▓ ▓▓▓▓ ▓▓▓▓   ▓▓▓▓▓▓▓▓   ▓▓▓▓
  ═══════════════════════════════════════════════
  lines gaps     TMA ions and     neighbours touch:
                 water get in     pattern collapse

  (swelling reported as a very important factor in collapse)
"#;
const SPOTS_5: &[Spot] = &[
    spot(
        r#"dry"#,
        0,
        0,
        r#"Lines as developed, with clear gaps between them."#,
    ),
    spot(
        r#"swollen"#,
        0,
        0,
        r#"TMA ions and water enter the resist and swell it, narrowing the gaps."#,
    ),
    spot(
        r#"pattern collapse"#,
        0,
        0,
        r#"When swollen lines are pulled together during rinse and dry they can stick, and the pattern is lost. See RINSE for the capillary forces."#,
    ),
    spot(
        r#"(swelling reported as a very important factor in collapse)"#,
        0,
        0,
        r#"The study reports swelling by TMA ions and water is a very important factor for pattern collapse."#,
    ),
];

const ART_6: &str = r#"# Develop sits inside the scanner loop

  scanner ══▶  ┌─────┐  ┌──────┐  ┌─────────┐  ┌───────┐
               │ PEB │─▶│ COOL │─▶│ DEVELOP │─▶│ RINSE │
               └─────┘  └──────┘  └─────────┘  └───────┘
               (track: throughput must match the scanner)

  track market share (aggregator estimate)
  TEL + Screen  ██████████████████████████████████ ~88%
  others        ▓▓▓▓ ~12%

  (EUV stochastic defects: missing contacts, bridges)
"#;
const SPOTS_6: &[Spot] = &[
    spot(
        r#"scanner ══▶"#,
        0,
        0,
        r#"ASML scanner output sets the pace: the track has to develop wafers as fast as they are exposed."#,
    ),
    spot(
        r#"DEVELOP"#,
        0,
        0,
        r#"The module this card is about: TMAH dispensed on a spinning wafer."#,
    ),
    spot(
        r#"TEL + Screen"#,
        0,
        TO_EOL,
        r#"Tokyo Electron (8035.T) leads and Screen (7735.T) is the only other major supplier. About 88% is an aggregator estimate."#,
    ),
    spot(
        r#"others"#,
        0,
        TO_EOL,
        r#"About 12% for everyone else (aggregator estimate)."#,
    ),
    spot(
        r#"(EUV stochastic defects: missing contacts, bridges)"#,
        0,
        0,
        r#"Few photons per pixel means random defects, so developer and rinse chemistry matter as much as the tool."#,
    ),
];

const ART_7: &str = r#"# The meniscus pulls lines together

  rinse liquid  ~~~~~~~~~~~~~~~~~~~~
                 ▓▓     ▓▓     ▓▓
   liquid ──▶   ▓▓ ◀──▶ ▓▓ ◀──▶ ▓▓    force pulls inward
                 ▓▓     ▓▓     ▓▓
   ══════════════════════════════════
                 |<-- S -->|

  capillary pressure   P = 2 x gamma x cos(theta) / S
  gamma = surface tension of the rinse   theta = contact angle
  S = space between lines (narrow S: bigger P)

  (collapse when capillary force beats the resist's adhesion)
"#;
const SPOTS_7: &[Spot] = &[
    spot(
        r#"rinse liquid"#,
        0,
        0,
        r#"Deionised water at first, which has high surface tension. Spin drying pulls the liquid edge down through the pattern."#,
    ),
    spot(
        r#"force pulls inward"#,
        0,
        0,
        r#"Liquid left between two lines pulls them toward each other. Unequal liquid heights between neighbours make the net force."#,
    ),
    spot(
        r#"P = 2 x gamma x cos(theta) / S"#,
        0,
        0,
        r#"The standard expression in the literature. Lower surface tension or a contact angle nearer 90 degrees lowers P."#,
    ),
    spot(
        r#"S = space between lines"#,
        0,
        0,
        r#"Narrower spaces give larger pressure, which is why shrinking pitch makes collapse worse."#,
    ),
];

const ART_8: &str = r#"# Critical aspect ratio before collapse

  water rinse         ███████████████████████ 2.5
  surfactant rinse    ██████████████████████████████ 3.2
                                              (+20-30%)

  aim: minimise 2 x gamma x cos(theta)

  lower gamma (surfactant)  ──▶ smaller P
  but low-gamma solvents often have small theta,
  so cos(theta) rises ──▶ the gain is partly lost

  supercritical CO2 drying removes surface tension entirely,
  but few 300 mm tools exist
"#;
const SPOTS_8: &[Spot] = &[
    spot(
        r#"water rinse"#,
        0,
        TO_EOL,
        r#"Baseline in one SPIE study: critical aspect ratio of about 2.5."#,
    ),
    spot(
        r#"surfactant rinse"#,
        0,
        TO_EOL,
        r#"Fluorosurfactants lowered surface tension and raised the critical aspect ratio to about 3.2 in the same study, a 20-30% gain."#,
    ),
    spot(
        r#"aim: minimise 2 x gamma x cos(theta)"#,
        0,
        0,
        r#"The study's conclusion: the best rinse minimises 2 gamma cos(theta), not just gamma."#,
    ),
    spot(
        r#"so cos(theta) rises"#,
        0,
        0,
        r#"This is the trade-off with solvents such as 2-propanol, and why a patent notes limits at modest aspect ratios."#,
    ),
    spot(
        r#"supercritical CO2 drying"#,
        0,
        0,
        r#"IBM slides call supercritical CO2 drying the ultimate surface-tension reduction, but limited commercial 300 mm tools are available."#,
    ),
];

const ART_9: &str = r#"# Thin resist trades collapse for photons

   thick resist            thin resist (High-NA)
      ▓▓  ▓▓
      ▓▓  ▓▓
      ▓▓  ▓▓                   ▓▓  ▓▓
      ▓▓  ▓▓                   ▓▓  ▓▓
   ══════════════           ══════════════
   high aspect ratio        low aspect ratio
   collapse risk: higher    collapse risk: lower
   photons absorbed: more   photons absorbed: fewer

  dry process: no wet develop, so no rinse meniscus (Lam claim)
"#;
const SPOTS_9: &[Spot] = &[
    spot(
        r#"thick resist"#,
        0,
        0,
        r#"More material in the beam path absorbs more EUV photons, but a tall thin line is easier to topple."#,
    ),
    spot(
        r#"thin resist (High-NA)"#,
        0,
        0,
        r#"A thinner film lowers the aspect ratio, which eases collapse, but captures fewer photons so shot noise rises."#,
    ),
    spot(
        r#"collapse risk: higher"#,
        0,
        0,
        r#"Capillary force acts over the line height, so tall lines are pulled over more easily."#,
    ),
    spot(
        r#"photons absorbed: fewer"#,
        0,
        0,
        r#"Fewer absorbed photons means more stochastic roughness and defects for the same dose."#,
    ),
    spot(
        r#"dry process: no wet develop, so no rinse meniscus (Lam claim)"#,
        0,
        0,
        r#"Lam's dry resist skips wet develop, so there is no capillary pull. This is a company claim, not independently verified here."#,
    ),
];

const ART_10: &str = r#"# Pattern transfer

  resist stencil          after etch            after strip
  ▓▓▓▓    ▓▓▓▓            ▓▓▓▓    ▓▓▓▓
  ████████████████        ▓▓▓▓    ▓▓▓▓          ████    ████
  ░░░░░░░░░░░░░░░░        ░░░░    ░░░░          ░░░░    ░░░░
  ═══════════════         ═══════════           ═══════════
  ▓ resist  █ hard mask   trenches cut          resist and mask
  ░ film to be etched     in the film           removed

  (roughness and lost resist height carry into the final line)
"#;
const SPOTS_10: &[Spot] = &[
    spot(
        r#"resist stencil"#,
        0,
        0,
        r#"The developed resist is only a temporary mask. It must survive long enough for the etch to cut the layer under it."#,
    ),
    spot(
        r#"▓ resist  █ hard mask"#,
        0,
        0,
        r#"Most EUV layers put a thin hard mask under the resist so the pattern survives etch (textbook)."#,
    ),
    spot(
        r#"after etch"#,
        0,
        0,
        r#"Plasma cuts the film only where the mask does not protect it."#,
    ),
    spot(
        r#"removed"#,
        0,
        0,
        r#"After etch the resist is stripped. Whatever roughness it had has been copied into the film."#,
    ),
    spot(
        r#"(roughness and lost resist height carry into the final line)"#,
        0,
        0,
        r#"Every nanometre of edge roughness or lost resist height in develop shows up in the final transistor or metal line."#,
    ),
];

const ART_11: &str = r#"# Yield learning loop

  ┌─────────┐   ┌─────────┐   ┌─────────┐
  │ EXPOSE  │──▶│ DEVELOP │──▶│  ETCH   │
  └─────────┘   └────┬────┘   └────┬────┘
        ▲            │ inspect     │ inspect
        │            ▼             ▼
        │        ┌─────────────────────┐
        └────────│ metrology + defect  │
   feedback      │ review (KLA tools)  │
                 └─────────────────────┘

  (bridges, missing contacts, mask defects, collapse, particles)
"#;
const SPOTS_11: &[Spot] = &[
    spot(
        r#"EXPOSE"#,
        0,
        0,
        r#"The scanner step. Dose and focus corrections come back from the measurements."#,
    ),
    spot(
        r#"DEVELOP"#,
        0,
        0,
        r#"First inspection point: defects that show here can be rework candidates."#,
    ),
    spot(
        r#"ETCH"#,
        0,
        0,
        r#"Second inspection point: some defects only show up after the pattern is cut into the film."#,
    ),
    spot(
        r#"metrology + defect"#,
        0,
        0,
        r#"Inspection and measurement tools catch defects at both points and feed settings back upstream (textbook)."#,
    ),
    spot(
        r#"(bridges, missing contacts, mask defects, collapse, particles)"#,
        0,
        0,
        r#"Defects found here come from every upstream step, which is why yield learning crosses litho, metrology and etch teams."#,
    ),
];

const ART_12: &str = r#"# One EUV layer, many tool sales

  coat ──▶ expose ──▶ develop ──▶ etch ──▶ inspect
   TEL      ASML        TEL       LRCX      KLAC
                                  TEL
                                  AMAT

  layers per chip rise ──▶ every column scales with it

  (vendors named are examples; see ETCH and KLAC pages)
"#;
const SPOTS_12: &[Spot] = &[
    spot(
        r#"coat"#,
        0,
        0,
        r#"Coater/developer track: Tokyo Electron leads."#,
    ),
    spot(
        r#"expose"#,
        0,
        0,
        r#"ASML is the sole EUV scanner supplier."#,
    ),
    spot(
        r#"develop"#,
        0,
        0,
        r#"Same track as coat, so TEL sells both ends of the litho cluster."#,
    ),
    spot(
        r#"etch"#,
        0,
        0,
        r#"Lam Research, Tokyo Electron and Applied Materials lead etch. See the ETCH page."#,
    ),
    spot(
        r#"inspect"#,
        0,
        0,
        r#"KLA leads process control. See the KLAC page."#,
    ),
    spot(
        r#"layers per chip rise"#,
        0,
        0,
        r#"Each extra EUV layer pulls through coat, develop, etch and metrology spending (textbook)."#,
    ),
];

const ART_13: &str = r#"# Bake, then cool, then develop

  temp
   ^
130 |      ┌────────┐
    |      │  PEB   │ acid keeps moving
    |      │        ╲
 23 |──────┘         ╲_______  COOL: reaction stops
    └────────────────────────▶ time
          (time between bake and cool is controlled)

  hot = acid diffuses = blur grows
  cool = acid frozen in place
"#;
const SPOTS_13: &[Spot] = &[
    spot(
        r#"PEB"#,
        0,
        0,
        r#"Hot plate stage: acid cuts protecting groups and also diffuses."#,
    ),
    spot(
        r#"COOL: reaction stops"#,
        0,
        0,
        r#"Cooling to room temperature freezes the acid. Until then diffusion still adds blur."#,
    ),
    spot(
        r#"(time between bake and cool is controlled)"#,
        0,
        0,
        r#"Because blur accumulates until the wafer is cool, the transfer time between bake and cool plates is part of the bake budget (textbook)."#,
    ),
    spot(
        r#"hot = acid diffuses"#,
        0,
        0,
        r#"Diffusivity rises with temperature, which is also why PEB temperature uniformity sets line width uniformity."#,
    ),
];

const ART_14: &str = r#"# Blur sigma = sqrt(2*D*t), D = 25 nm2/s (computed)

  10 s    ████████████ 22 nm
  30 s    ████████████████████ 39 nm
  60 s    ████████████████████████████ 55 nm
  120 s   ████████████████████████████████████████ 77 nm

  EUV critical dimensions are only about 8-13 nm
  (one fitted D at one temperature, not any production resist)
"#;
const SPOTS_14: &[Spot] = &[
    spot(
        r#"10 s"#,
        0,
        TO_EOL,
        r#"sigma = sqrt(2 x 25 x 10) = 22 nm (computed)."#,
    ),
    spot(
        r#"30 s"#,
        0,
        TO_EOL,
        r#"sigma = sqrt(2 x 25 x 30) = 39 nm (computed)."#,
    ),
    spot(
        r#"60 s"#,
        0,
        TO_EOL,
        r#"sigma = sqrt(2 x 25 x 60) = 55 nm (computed)."#,
    ),
    spot(
        r#"120 s"#,
        0,
        TO_EOL,
        r#"sigma = sqrt(2 x 25 x 120) = 77 nm (computed)."#,
    ),
    spot(
        r#"EUV critical dimensions are only about 8-13 nm"#,
        0,
        0,
        r#"The raw formula overshoots feature size, which shows real resists must be tuned with quencher, lower temperature and lower diffusivity polymers."#,
    ),
];

const ART_15: &str = r#"# Plate uniformity across the wafer

  cool plate, top view         develop rate follows temperature

   ░ ░ ░ ░ ░                   warm spot ──▶ faster dissolve
  ░ ░ ▓ ▓ ░ ░                                 ──▶ wider line
   ░ ▓ ▓ ▓ ░                   cool spot ──▶ slower dissolve
  ░ ░ ▓ ▓ ░ ░                                 ──▶ narrower line
   ░ ░ ░ ░ ░
  ▓ warm  ░ at setpoint

  tenths of a degree or seconds shift critical dimension
"#;
const SPOTS_15: &[Spot] = &[
    spot(
        r#"cool plate, top view"#,
        0,
        0,
        r#"Wafer-wide temperature differences at the cool plate turn into critical-dimension differences."#,
    ),
    spot(
        r#"warm spot"#,
        0,
        0,
        r#"TMAH dissolution rate depends on temperature (textbook), so warmer regions develop faster."#,
    ),
    spot(
        r#"cool spot"#,
        0,
        0,
        r#"Cooler regions develop more slowly, so critical dimension drifts the other way."#,
    ),
    spot(
        r#"tenths of a degree or seconds shift critical dimension"#,
        0,
        0,
        r#"Track vendors compete on bake and cool uniformity and throughput for this reason."#,
    ),
];

const ART_16: &str = r#"# Quencher neutralises stray acid

   exposed        edge         unexposed
   H+ H+ H+ H+ ──▶ H+ ──▶ H+ ··▶
                    │       ▲
                    ▼       │ quencher (weak base Q)
              H+ + Q ──▶ HQ+   no longer cuts

  without Q: acid wanders into unexposed side, edge blurs
  with Q:    acid stops at the edge, sharper boundary
             (but the lost acid is lost sensitivity)
"#;
const SPOTS_16: &[Spot] = &[
    spot(
        r#"H+ H+ H+ H+"#,
        0,
        0,
        r#"Photoacid made by exposure inside the exposed region."#,
    ),
    spot(
        r#"quencher (weak base Q)"#,
        0,
        0,
        r#"A weak base distributed through the resist that reacts with acid before it travels far (textbook)."#,
    ),
    spot(
        r#"H+ + Q ──▶ HQ+"#,
        0,
        0,
        r#"A neutralised acid no longer catalyses deprotection."#,
    ),
    spot(
        r#"without Q"#,
        0,
        0,
        r#"Acid migrates into the unexposed region, blurring the boundary."#,
    ),
    spot(
        r#"(but the lost acid is lost sensitivity)"#,
        0,
        0,
        r#"Neutralised acid is acid that does not cut protecting groups, so more dose is needed."#,
    ),
];

const ART_17: &str = r#"# Blur versus dose

  more quencher                        less quencher
  ◀────────────────────────────────────────────────▶
  sharp edge                           blurry edge
  low roughness                        rough edges
  HIGH dose needed                     low dose needed
  (slow, fewer wafers/hour)            (fast, but lower resolution)

  defects also come from uneven PAG and quencher
  distribution and uneven acid diffusion, not only photon noise
"#;
const SPOTS_17: &[Spot] = &[
    spot(
        r#"more quencher"#,
        0,
        0,
        r#"Shorter acid reach gives a sharper edge but needs more exposure dose."#,
    ),
    spot(
        r#"less quencher"#,
        0,
        0,
        r#"Acid reaches further, so less dose is needed, but resolution and edge roughness get worse."#,
    ),
    spot(
        r#"HIGH dose needed"#,
        0,
        0,
        r#"Higher dose means slower scanner throughput and more cost per wafer (textbook inference)."#,
    ),
    spot(
        r#"defects also come from uneven PAG and quencher"#,
        0,
        0,
        r#"Chemical stochastics research lists uneven PAG and quencher distribution and uneven diffusion as separate defect causes, besides photon shot noise."#,
    ),
];

const ART_18: &str = r#"# CAR versus metal-oxide resist

               CAR                    MOR
  EUV absorb   ███████ 1x             █████████████████████ ~3x
  acid blur    yes (smooths edges)    none
  edge rough   smoothed by blur       stays rough
  profile      normal                 can undercut (top absorbs)

  (MOR numbers from a simulation study cited on the page)
"#;
const SPOTS_18: &[Spot] = &[
    spot(
        r#"EUV absorb"#,
        0,
        TO_EOL,
        r#"MOR absorbs about 3x more EUV than CAR, so it catches more photons per nm of film."#,
    ),
    spot(
        r#"acid blur"#,
        0,
        TO_EOL,
        r#"CAR has acid blur that smooths edges at the cost of resolution. MOR has none."#,
    ),
    spot(
        r#"edge rough"#,
        0,
        TO_EOL,
        r#"Without blur smoothing, MOR edges stay rough in the simulation study."#,
    ),
    spot(
        r#"profile"#,
        0,
        TO_EOL,
        r#"Strong absorption at the top can leave an undercut profile (simulation study)."#,
    ),
    spot(
        r#"(MOR numbers from a simulation study cited on the page)"#,
        0,
        0,
        r#"Simulation results, so treat as indicative."#,
    ),
];

const ART_19: &str = r#"# TMAH, the metal-free base

         CH3
          |
  CH3 ── N+ ── CH3      OH-
          |             hydroxide
         CH3
   tetramethylammonium

  NaOH:  Na+ OH-   sodium can contaminate transistors
  TMAH:  organic cation, no metal ions (textbook)

  standard use: 2.38 wt% in water
"#;
const SPOTS_19: &[Spot] = &[
    spot(
        r#"tetramethylammonium"#,
        0,
        0,
        r#"Four methyl groups around one nitrogen. The cation is organic, so it carries no metal."#,
    ),
    spot(
        r#"OH-"#,
        0,
        0,
        r#"The hydroxide is what takes the proton from the polymer acid groups and makes them dissolve."#,
    ),
    spot(
        r#"NaOH:"#,
        0,
        TO_EOL,
        r#"A sodium base would leave mobile metal ions that can contaminate transistors (textbook)."#,
    ),
    spot(
        r#"TMAH:"#,
        0,
        TO_EOL,
        r#"This is why TMAH is used: no metal ions (textbook)."#,
    ),
    spot(
        r#"standard use: 2.38 wt% in water"#,
        0,
        0,
        r#"The standard developer concentration."#,
    ),
];

const ART_20: &str = r#"# TMAH market estimates (USD, low reliability)

  one report, 2025   ███████████████████████ 1.16B
  one report, 2032   ████████████████████████████████████████ 1.98B
  other summary      ███████ 0.35-0.70B (2025)
  other estimate     ████████████████████████████████████ 1.8B

  estimates differ by a factor of 3 or more
  (definitions and scope differ between reports)
"#;
const SPOTS_20: &[Spot] = &[
    spot(
        r#"one report, 2025"#,
        0,
        TO_EOL,
        r#"Quoted on the page: USD 1.16B in 2025."#,
    ),
    spot(
        r#"one report, 2032"#,
        0,
        TO_EOL,
        r#"The same report projects USD 1.98B by 2032."#,
    ),
    spot(
        r#"other summary"#,
        0,
        TO_EOL,
        r#"Another summary of the same listing gives roughly USD 350-700 million for 2025."#,
    ),
    spot(
        r#"other estimate"#,
        0,
        TO_EOL,
        r#"Other sources give USD 1.8B. Estimates vary widely."#,
    ),
    spot(
        r#"estimates differ by a factor of 3 or more"#,
        0,
        0,
        r#"Low reliability: treat these only as an order-of-magnitude range."#,
    ),
];

const ART_21: &str = r#"# Developer supply

  Merck KGaA (MRK.DE)       listed producer
  BASF (BAS.DE)             listed producer
  Mitsubishi Gas Chemical   listed producer
  Tokuyama                  Chinese subsidiary ~13,000 t/yr
  SACHEM                    high-purity quaternary ammonium
  FUJIFILM                  2.38 wt% ready-to-use grades

  chokepoint: metal-ion purity (no ppb specs found)
  risk: TMAH waste rules (textbook)
"#;
const SPOTS_21: &[Spot] = &[
    spot(
        r#"Merck KGaA (MRK.DE)"#,
        0,
        0,
        r#"Named as a TMAH producer in the page's lists."#,
    ),
    spot(
        r#"BASF (BAS.DE)"#,
        0,
        0,
        r#"Named as a TMAH producer in the page's lists."#,
    ),
    spot(
        r#"Mitsubishi Gas Chemical"#,
        0,
        0,
        r#"Named as a TMAH producer in the page's lists."#,
    ),
    spot(
        r#"Tokuyama"#,
        0,
        0,
        r#"Its Chinese subsidiary has about 13,000 tons per year of TMAH capacity."#,
    ),
    spot(
        r#"SACHEM"#,
        0,
        0,
        r#"Supplier of high-purity quaternary ammonium compounds."#,
    ),
    spot(
        r#"FUJIFILM"#,
        0,
        0,
        r#"Sells 2.38 wt% ready-to-use developers, a 24.9% concentrate, and metal-ion and metal-ion-free grades including an ultra-high-purity grade."#,
    ),
    spot(
        r#"chokepoint: metal-ion purity (no ppb specs found)"#,
        0,
        0,
        r#"The page lists developer purity as a chokepoint, but no supplier ppb specifications were found."#,
    ),
];

const ART_22: &str = r#"# Acid spreads like a Gaussian

  acid
  count
    ^        ┌─────┐
    |      ╱         ╲        narrow = small D or short t
    |    ╱             ╲
    |  ╱                 ╲    wide = large D or long t
    └─────────────────────────▶ distance from the exposed spot
              |<-sigma->|

  sigma = sqrt(2 x D x t)
  D = 25 nm2/s (one commercial polymer CAR)
  (linewidth vs bake time was non-linear: model is rough)
"#;
const SPOTS_22: &[Spot] = &[
    spot(
        r#"acid"#,
        0,
        0,
        r#"The amount of acid at each distance from where it was generated."#,
    ),
    spot(
        r#"narrow = small D or short t"#,
        0,
        0,
        r#"Low diffusivity or a short bake keeps the acid close to where the photon hit."#,
    ),
    spot(
        r#"wide = large D or long t"#,
        0,
        0,
        r#"High diffusivity or a long bake spreads it, blurring the latent image."#,
    ),
    spot(
        r#"sigma = sqrt(2 x D x t)"#,
        0,
        0,
        r#"The Gaussian blur length for acid diffusion in time t with diffusivity D."#,
    ),
    spot(
        r#"(linewidth vs bake time was non-linear: model is rough)"#,
        0,
        0,
        r#"The same study found linewidth versus bake time was non-linear, so treat the Gaussian as an illustration."#,
    ),
];

const ART_23: &str = r#"# sigma at D = 25 nm2/s (computed)

  10 s    ████████████ 22 nm
  30 s    ████████████████████ 39 nm
  60 s    ████████████████████████████ 55 nm
  120 s   ████████████████████████████████████████ 77 nm

  EUV feature size  █████ 8-13 nm

  real resists beat this with quencher, lower temperature
  and lower diffusivity polymers
"#;
const SPOTS_23: &[Spot] = &[
    spot(
        r#"10 s"#,
        0,
        TO_EOL,
        r#"sqrt(2 x 25 x 10) = 22 nm (computed)."#,
    ),
    spot(
        r#"30 s"#,
        0,
        TO_EOL,
        r#"sqrt(2 x 25 x 30) = 39 nm (computed)."#,
    ),
    spot(
        r#"60 s"#,
        0,
        TO_EOL,
        r#"sqrt(2 x 25 x 60) = 55 nm (computed)."#,
    ),
    spot(
        r#"120 s"#,
        0,
        TO_EOL,
        r#"sqrt(2 x 25 x 120) = 77 nm (computed)."#,
    ),
    spot(
        r#"EUV feature size"#,
        0,
        TO_EOL,
        r#"EUV critical dimensions are about 8-13 nm, far below these blur lengths, so the formula overstates blur for real tuned resists."#,
    ),
];

const ART_24: &str = r#"# Same formula, 100-1000x lower D (computed)

  D = 25 nm2/s     1 s ▶ sigma 7.1 nm   hot-plate extrapolation
  D = 0.25 nm2/s   1 s ▶ sigma 0.7 nm   laser, 100x lower
  D = 0.025 nm2/s  1 s ▶ sigma 0.2 nm   laser, 1000x lower

  blur   hot  ████████████████████████████████ 7.1 nm
         100x ███ 0.7 nm
         1000x▏ 0.2 nm

  (extrapolated from one D; laser PEB is a research result)
"#;
const SPOTS_24: &[Spot] = &[
    spot(
        r#"D = 25 nm2/s     1 s"#,
        0,
        TO_EOL,
        r#"sqrt(2 x 25 x 1) = 7.1 nm (computed)."#,
    ),
    spot(
        r#"D = 0.25 nm2/s"#,
        0,
        TO_EOL,
        r#"100x lower diffusivity gives sigma = 0.7 nm over 1 s (computed)."#,
    ),
    spot(
        r#"D = 0.025 nm2/s"#,
        0,
        TO_EOL,
        r#"1000x lower diffusivity gives sigma = 0.2 nm over 1 s (computed)."#,
    ),
    spot(
        r#"(extrapolated from one D; laser PEB is a research result)"#,
        0,
        0,
        r#"These values extend the page's number and the ORNL-linked study's claim, so they are indicative only."#,
    ),
];

const ART_25: &str = r#"# PEB module cross-section

         wafer, resist side up
     ══════════════════════════════
          proximity gap (no contact)
     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
     ▓▓▓▓▓ HOT PLATE 90-150 C ▓▓▓▓▓▓
     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
         heater zones + sensors

  bake 30-120 s     uniformity across 300 mm is the key spec
"#;
const SPOTS_25: &[Spot] = &[
    spot(
        r#"wafer, resist side up"#,
        0,
        0,
        r#"The resist-coated wafer sits face up above the plate."#,
    ),
    spot(
        r#"proximity gap (no contact)"#,
        0,
        0,
        r#"A small gap lets heat transfer evenly without pressing the wafer against metal."#,
    ),
    spot(
        r#"HOT PLATE 90-150 C"#,
        0,
        0,
        r#"Typical CAR bake range from the SPIE paper."#,
    ),
    spot(
        r#"heater zones + sensors"#,
        0,
        0,
        r#"Zoned heating and sensing keep the plate uniform (textbook)."#,
    ),
    spot(
        r#"uniformity across 300 mm is the key spec"#,
        0,
        0,
        r#"Bake temperature shifts critical dimension through acid diffusion, so non-uniformity becomes line-width non-uniformity."#,
    ),
];

const ART_26: &str = r#"# Track share

  EUV tracks (TrendForce, reported)
  TEL           ████████████████████████████████████ ~100%

  coater/developer sales (aggregators, 88-91%)
  TEL + Screen  ████████████████████████████████ ~88-91%
  others        ▓▓▓ ~9-12%

  TEL product: LITHIUS Pro Z, 300 mm, EUV-capable
  (no independent share figure found)
"#;
const SPOTS_26: &[Spot] = &[
    spot(
        r#"TEL           ████"#,
        0,
        TO_EOL,
        r#"TrendForce is cited for TEL at reportedly about 100% of EUV tracks."#,
    ),
    spot(
        r#"TEL + Screen"#,
        0,
        TO_EOL,
        r#"Aggregator reports put the two at about 88-91% of coater/developer sales (estimates)."#,
    ),
    spot(r#"others"#, 0, TO_EOL, r#"Roughly the remaining 9-12%."#),
    spot(
        r#"TEL product: LITHIUS Pro Z, 300 mm, EUV-capable"#,
        0,
        0,
        r#"Marketed for 10 nm and beyond with better defectivity, productivity and cost of ownership."#,
    ),
    spot(
        r#"(no independent share figure found)"#,
        0,
        0,
        r#"The share numbers come from a news item and aggregator reports, not a primary source."#,
    ),
];

const ART_27: &str = r#"# Track and scanner run in lockstep

  scanner  ████████████████████████ 220 wafers/hour
  track    ████████████████████████ must match
           (coat, bake, cool, develop in parallel modules)

  more bake plates ──▶ more wafers in flight
  slower plate time ──▶ lower hourly output

  alternative: ms laser bake, under half the EUV dose
  (research only)
"#;
const SPOTS_27: &[Spot] = &[
    spot(
        r#"scanner  ████"#,
        0,
        TO_EOL,
        r#"The page states 220 wafers per hour as the scanner pace the track must match."#,
    ),
    spot(
        r#"track    ████"#,
        0,
        TO_EOL,
        r#"Tracks use several parallel modules so that bake and develop do not slow the scanner."#,
    ),
    spot(
        r#"more bake plates"#,
        0,
        0,
        r#"Parallel plates put more wafers in flight at once (textbook)."#,
    ),
    spot(
        r#"slower plate time"#,
        0,
        0,
        r#"Longer bake times reduce hourly output unless more plates are added."#,
    ),
    spot(
        r#"alternative: ms laser bake, under half the EUV dose"#,
        0,
        0,
        r#"One ORNL-linked study reports this, but production use is unproven."#,
    ),
];

const ART_28: &str = r#"# Develop module

        nozzle
          |  TMAH puddle or spray
          v
     ══════════════════  wafer spins slowly
        ┌────────┐
        │ CHUCK  │  vacuum holds the wafer
        └───┬────┘
   ┌────────┴────────┐
   │  cup + drain    │──▶ TMAH-bearing waste
   └─────────────────┘
"#;
const SPOTS_28: &[Spot] = &[
    spot(
        r#"nozzle"#,
        0,
        0,
        r#"Dispenses TMAH over the wafer as a puddle or spray."#,
    ),
    spot(
        r#"wafer spins slowly"#,
        0,
        0,
        r#"Slow rotation helps spread the developer evenly (page)."#,
    ),
    spot(
        r#"CHUCK"#,
        0,
        0,
        r#"A vacuum chuck holds the wafer while it spins."#,
    ),
    spot(
        r#"cup + drain"#,
        0,
        0,
        r#"Collects the effluent, which carries dissolved resist and TMAH."#,
    ),
    spot(
        r#"TMAH-bearing waste"#,
        0,
        0,
        r#"Developer waste is a TMAH-bearing stream with regulatory limits (textbook)."#,
    ),
];

const ART_29: &str = r#"# What must be equal everywhere

  centre ──────────────── edge
  concentration   same?
  temperature     same?
  contact time    same?

  if not: critical dimension drifts centre to edge

  defects born here
  bubbles   particles   scum (residue)   watermarks (drying)
"#;
const SPOTS_29: &[Spot] = &[
    spot(
        r#"concentration"#,
        0,
        0,
        r#"Developer strength must match at every point on the wafer."#,
    ),
    spot(
        r#"temperature"#,
        0,
        0,
        r#"TMAH dissolution rate depends on temperature (textbook)."#,
    ),
    spot(
        r#"contact time"#,
        0,
        0,
        r#"How long each region sits in developer sets how much dissolves."#,
    ),
    spot(
        r#"bubbles"#,
        0,
        0,
        r#"Trapped bubbles block developer and leave unexposed spots."#,
    ),
    spot(
        r#"scum (residue)"#,
        0,
        0,
        r#"Thin leftover resist residue in what should be clear spaces."#,
    ),
    spot(
        r#"watermarks (drying)"#,
        0,
        0,
        r#"Drying marks from water left on the surface (textbook)."#,
    ),
];

const ART_30: &str = r#"# Each scanner pulls track modules with it

  ASML scanner ──▶ ┌──────────────────┐
                   │ TEL track        │
                   │ coat bake cool   │
                   │ develop rinse    │
                   └──────────────────┘

  EUV tracks      TEL ~100% (TrendForce, reported)
  all tracks      TEL + Screen ~88-91% (aggregators)

  rinse: fluorosurfactant raised critical aspect ratio 20-30%
"#;
const SPOTS_30: &[Spot] = &[
    spot(
        r#"ASML scanner"#,
        0,
        0,
        r#"ASML is the only EUV scanner supplier. Every scanner needs a track beside it."#,
    ),
    spot(
        r#"TEL track"#,
        0,
        0,
        r#"Tokyo Electron (8035.T) CLEAN TRACK with coat, bake, cool, develop and rinse modules."#,
    ),
    spot(
        r#"EUV tracks"#,
        0,
        TO_EOL,
        r#"TrendForce is cited for TEL at reportedly about 100% of EUV tracks."#,
    ),
    spot(
        r#"all tracks"#,
        0,
        TO_EOL,
        r#"Aggregator estimates for TEL plus SCREEN at 88-91% of coater/developer sales."#,
    ),
    spot(
        r#"rinse: fluorosurfactant raised critical aspect ratio 20-30%"#,
        0,
        0,
        r#"Result from one SPIE rinse-material study."#,
    ),
];

const ART_31: &str = r#"# MOR versus CAR, schematic cross-sections

  CAR: gradual absorption       MOR: top absorbs most
   photons ▼ ▼ ▼ ▼               photons ▼ ▼ ▼ ▼
   ░░░░░░░░░░░░                  ████████████
   ░░░░░░░░░░░░                  ▒▒▒▒▒▒▒▒▒▒▒▒
   ░░░░░░░░░░░░                  ░░░░░░░░░░░░
   even exposure, blur smooths   undercut profile possible
   absorbs 1x                    absorbs about 3x
  (simulation study cited on the page)
"#;
const SPOTS_31: &[Spot] = &[
    spot(
        r#"CAR: gradual absorption"#,
        0,
        0,
        r#"Chemically amplified resists absorb less, so more of the film's depth is exposed evenly."#,
    ),
    spot(
        r#"MOR: top absorbs most"#,
        0,
        0,
        r#"Metal-oxide resists absorb about 3x more EUV, mostly near the top."#,
    ),
    spot(
        r#"undercut profile possible"#,
        0,
        0,
        r#"Strong top absorption can leave an undercut profile (simulation study)."#,
    ),
    spot(
        r#"absorbs about 3x"#,
        0,
        0,
        r#"More photons captured per nm of film."#,
    ),
    spot(
        r#"(simulation study cited on the page)"#,
        0,
        0,
        r#"Results come from simulation, so treat them as indicative."#,
    ),
];

const ART_32: &str = r#"# Sensitivity, roughness, defects

  dose up    ──▶ fewer defects, but film thins after develop
  dose down  ──▶ faster scanning, but more stochastic defects

  defect probability
    ^                              .
    |                         .
    |                    .
    |             .
    └───────────────────────────────▶ feature size shrinks
  (Monte Carlo study: rises exponentially as features shrink)

  High-NA: thinner resist ──▶ fewer photons ──▶ rougher
"#;
const SPOTS_32: &[Spot] = &[
    spot(
        r#"dose up"#,
        0,
        TO_EOL,
        r#"Higher dose helps, but raising CAR dose also thins the film after develop, leaving less resist for etch."#,
    ),
    spot(
        r#"dose down"#,
        0,
        TO_EOL,
        r#"Lower dose raises throughput but reports show a strong trade-off between sensitivity and defectivity."#,
    ),
    spot(
        r#"defect probability"#,
        0,
        0,
        r#"A Monte Carlo study finds defect probability rises exponentially with decreasing feature size."#,
    ),
    spot(
        r#"High-NA: thinner resist"#,
        0,
        0,
        r#"Thinner resists capture fewer photons, which can worsen roughness."#,
    ),
];

const ART_33: &str = r#"# Who is in resists

  JSR / Inpria   leading MOR supplier (textbook)
                 Sept 2025 cross-licence with Lam
  TOK            resist maker (textbook)
  Shin-Etsu      resist maker (textbook)
  Sumitomo Chem  resist maker (textbook)
  Lam Research   dry resist (Aether), see next card

  High-NA: stochastics limit yield, so resist is the battleground
"#;
const SPOTS_33: &[Spot] = &[
    spot(
        r#"JSR / Inpria"#,
        0,
        TO_EOL,
        r#"JSR/Inpria is described as the leading metal-oxide resist supplier (textbook). Lam and JSR/Inpria signed a cross-licence in September 2025 (JSR press release)."#,
    ),
    spot(
        r#"TOK"#,
        0,
        TO_EOL,
        r#"Resist maker, from the page's textbook list (not sourced here)."#,
    ),
    spot(
        r#"Shin-Etsu"#,
        0,
        TO_EOL,
        r#"Resist maker, from the page's textbook list (not sourced here)."#,
    ),
    spot(
        r#"Sumitomo Chem"#,
        0,
        TO_EOL,
        r#"Resist maker, from the page's textbook list (not sourced here)."#,
    ),
    spot(
        r#"Lam Research"#,
        0,
        TO_EOL,
        r#"Lam's Aether dry resist deposits and develops resist without wet chemistry."#,
    ),
];

const ART_34: &str = r#"# Wet versus dry resist flow

  wet    coat (spin)──▶ expose ──▶ bake ──▶ develop (TMAH) ──▶ rinse
         liquid resist                      wet chemistry

  dry    deposit (vacuum) ──▶ expose ──▶ develop (dry etch)
         no spin coat, no TMAH, no rinse

  claim: 5-10x less chemicals than wet processes (Lam)
  Jan 2025: unnamed leading memory maker adopts it for DRAM
"#;
const SPOTS_34: &[Spot] = &[
    spot(
        r#"wet    coat"#,
        0,
        TO_EOL,
        r#"Conventional flow: spin on liquid resist, bake, develop in TMAH and rinse."#,
    ),
    spot(
        r#"dry    deposit"#,
        0,
        TO_EOL,
        r#"Aether deposits the resist in vacuum and develops it without wet chemistry."#,
    ),
    spot(
        r#"no spin coat, no TMAH, no rinse"#,
        0,
        0,
        r#"Skipping the wet steps removes the TMAH waste stream and the rinse meniscus."#,
    ),
    spot(
        r#"claim: 5-10x less chemicals than wet processes (Lam)"#,
        0,
        0,
        r#"Company claim, per the page."#,
    ),
    spot(
        r#"Jan 2025: unnamed leading memory maker adopts it for DRAM"#,
        0,
        0,
        r#"Reported by Storage Newsletter, February 2025."#,
    ),
];

const ART_35: &str = r#"# What dry resist could buy

  no wet develop  ──▶ no rinse meniscus ──▶ no capillary collapse
                      (reasoned, not verified here)
  no TMAH         ──▶ less chemical waste
  thin, even film ──▶ fits High-NA's shallow depth of focus

  open question: stochastics of a metal-containing resist
  at volume, beyond one memory customer
"#;
const SPOTS_35: &[Spot] = &[
    spot(
        r#"no wet develop"#,
        0,
        TO_EOL,
        r#"Reasoned from the rinse mechanism: no wet develop means no meniscus pulling lines together. Not verified here."#,
    ),
    spot(
        r#"no TMAH"#,
        0,
        TO_EOL,
        r#"Lam's lower chemical use claim implies less TMAH-bearing waste."#,
    ),
    spot(
        r#"thin, even film"#,
        0,
        TO_EOL,
        r#"High-NA has shallow depth of focus, so a thin well-controlled film is valuable."#,
    ),
    spot(
        r#"open question: stochastics of a metal-containing resist"#,
        0,
        0,
        r#"Unproven at scale: so far one unnamed memory maker has adopted it."#,
    ),
];

const ART_36: &str = r#"# Share if dry resist spreads

              today           if adoption widens
  Lam (LRCX)  new revenue     ▲ gains a litho-adjacent line
  TEL         track + develop ▼ loses the develop module
  TMAH makers developer sales ▼ lower volume
  JSR/Inpria  MOR supplier    ◆ cross-licence with Lam, Sept 2025

  (the downside cases are reasoning, not sourced)
"#;
const SPOTS_36: &[Spot] = &[
    spot(
        r#"Lam (LRCX)"#,
        0,
        TO_EOL,
        r#"A new EUV-adjacent revenue line if dry resist is adopted widely."#,
    ),
    spot(
        r#"TEL "#,
        0,
        TO_EOL,
        r#"If develop moves into a dry tool, the track loses that module (reasoning, not sourced)."#,
    ),
    spot(
        r#"TMAH makers"#,
        0,
        TO_EOL,
        r#"Developer chemical volumes would fall for dry-resist layers (reasoning, not sourced)."#,
    ),
    spot(
        r#"JSR/Inpria"#,
        0,
        TO_EOL,
        r#"JSR and Lam signed a cross-licence on 16 September 2025 (JSR press release)."#,
    ),
    spot(
        r#"(the downside cases are reasoning, not sourced)"#,
        0,
        0,
        r#"Adoption beyond one memory customer has not been shown."#,
    ),
];

const ART_37: &str = r#"# Concentration by layer of the supply chain

  tracks     TEL ~100% of EUV (TrendForce); TEL + Screen 88-91%
  developer  Merck KGaA, BASF, Tokuyama, Mitsubishi Gas, SACHEM
             FUJIFILM: 2.38 wt% incl. ultra-high-purity
  resists    JSR/Inpria, TOK, Shin-Etsu, Sumitomo (textbook)

  purity: metal ions can ruin transistors (textbook)
  (no supplier ppb specs found)
"#;
const SPOTS_37: &[Spot] = &[
    spot(
        r#"tracks"#,
        0,
        TO_EOL,
        r#"TEL reportedly makes about 100% of EUV tracks (TrendForce). With SCREEN, about 88-91% of coater/developer sales (aggregators)."#,
    ),
    spot(
        r#"developer"#,
        0,
        TO_EOL,
        r#"Developer supply spans several chemical makers, but purity grades narrow the field."#,
    ),
    spot(
        r#"resists"#,
        0,
        TO_EOL,
        r#"Japan-heavy supply from the page's textbook list."#,
    ),
    spot(
        r#"purity: metal ions can ruin transistors (textbook)"#,
        0,
        0,
        r#"Metal contamination is why TMAH replaced sodium-based developers."#,
    ),
    spot(
        r#"(no supplier ppb specs found)"#,
        0,
        0,
        r#"Supplier purity specifications were not found in public sources."#,
    ),
];

const ART_38: &str = r#"# Risk map

  stochastic defects  ──▶ High-NA yield
  resist cost         ──▶ per-wafer cost
  TMAH waste rules    ──▶ cost, permits (textbook)
  PFAS rules          ──▶ fluorosurfactant rinses?
                          (reasoning, not sourced)
  China TMAH capacity ──▶ Tokuyama subsidiary ~13,000 t/yr
"#;
const SPOTS_38: &[Spot] = &[
    spot(
        r#"stochastic defects"#,
        0,
        TO_EOL,
        r#"Few photons per pixel makes random defects that limit High-NA yield."#,
    ),
    spot(
        r#"resist cost"#,
        0,
        TO_EOL,
        r#"New resists such as metal-oxide cost more per wafer (textbook)."#,
    ),
    spot(
        r#"TMAH waste rules"#,
        0,
        TO_EOL,
        r#"TMAH is an environmental rule risk (textbook)."#,
    ),
    spot(
        r#"PFAS rules"#,
        0,
        TO_EOL,
        r#"Fluorosurfactants used for collapse mitigation may intersect with PFAS regulation. This is reasoning, not sourced."#,
    ),
    spot(
        r#"China TMAH capacity"#,
        0,
        TO_EOL,
        r#"Tokuyama's Chinese subsidiary has about 13,000 tons per year capacity."#,
    ),
];

const ART_39: &str = r#"# Same region, same dependency

  ASML scanner ◀── needs ──┬── TEL track          (Japan)
  (Netherlands)            ├── resists: JSR, TOK,  (Japan)
                           │   Shin-Etsu, Sumitomo
                           └── developer: Tokuyama,(Japan)
                               Mitsubishi Gas
  a shock to one region hits every EUV layer
  (Merck KGaA, BASF: Germany; SACHEM: US)
"#;
const SPOTS_39: &[Spot] = &[
    spot(
        r#"ASML scanner"#,
        0,
        0,
        r#"The scanner is only useful with a track, resist and developer beside it."#,
    ),
    spot(r#"TEL track"#, 0, 0, r#"Tokyo Electron, Japan."#),
    spot(
        r#"resists: JSR, TOK,"#,
        0,
        0,
        r#"Resist makers named in the page's textbook list, headquartered in Japan."#,
    ),
    spot(
        r#"developer: Tokuyama,"#,
        0,
        0,
        r#"Developer suppliers include Japanese makers, plus Merck KGaA and BASF in Germany."#,
    ),
    spot(
        r#"a shock to one region hits every EUV layer"#,
        0,
        0,
        r#"The page's conclusion: a geopolitical or disaster shock hits the same cluster that scanners depend on."#,
    ),
];

const ART_40: &str = r#"# Pattern moves resist, hard mask, film

  resist      ▓▓▓▓    ▓▓▓▓     soft and thin, erodes fast
  hard mask   ████    ████     carbon, nitride, oxide or metal
  film        ░░░░░░░░░░░░     the layer to carve
  stop layer  ════════════

  1  litho prints the resist
  2  a short etch copies it into the hard mask
  3  the mask survives the long film etch
"#;
const SPOTS_40: &[Spot] = &[
    spot(
        r#"resist      ▓▓▓▓"#,
        0,
        TO_EOL,
        r#"Too soft to survive a long, deep etch, so it is used only to pattern the harder layer below."#,
    ),
    spot(
        r#"hard mask   ████"#,
        0,
        TO_EOL,
        r#"A harder layer (carbon, nitride, oxide or metal, textbook) that erodes far more slowly than the film."#,
    ),
    spot(
        r#"film        ░░░░"#,
        0,
        TO_EOL,
        r#"The layer that will actually be carved."#,
    ),
    spot(
        r#"1  litho prints the resist"#,
        0,
        0,
        r#"Exposure and develop leave the resist stencil."#,
    ),
    spot(
        r#"3  the mask survives the long film etch"#,
        0,
        0,
        r#"This is the whole point of the hard mask."#,
    ),
];

const ART_41: &str = r#"# Mask thickness needed for a 10 um deep etch

  selectivity = film etch rate / mask etch rate

  selectivity 5:1    mask ██████████ 2.0 um
  selectivity 10:1   mask █████ 1.0 um
  selectivity 20:1   mask ██▌ 0.5 um
  (arithmetic from the definition, not a measured spec)

  NAND channel hole: ~10 um deep, opening ~100 nm
  a thick mask over a 100 nm opening is itself hard to open
"#;
const SPOTS_41: &[Spot] = &[
    spot(
        r#"selectivity 5:1"#,
        0,
        TO_EOL,
        r#"10 um of film etched at 5:1 erodes 2 um of mask (arithmetic)."#,
    ),
    spot(
        r#"selectivity 10:1"#,
        0,
        TO_EOL,
        r#"At 10:1, 1 um of mask is consumed (arithmetic)."#,
    ),
    spot(
        r#"selectivity 20:1"#,
        0,
        TO_EOL,
        r#"At 20:1, 0.5 um of mask is consumed (arithmetic)."#,
    ),
    spot(
        r#"NAND channel hole: ~10 um deep, opening ~100 nm"#,
        0,
        0,
        r#"Figures from the cryo-etch article on the page."#,
    ),
];

const ART_42: &str = r#"# Errors baked in here stay forever

  litho layer ──▶ etch ──▶ clean       repeated per layer

  errors copied at etch (cannot be fixed later)
    mask faceting     LER      CD drift

  more steps per wafer
    GAA logic  ▶ more mask layers per node
    NAND       ▶ ~30% more word lines per generation
                 (cryo-etch article)
  ──▶ etch demand scales with litho layer count (textbook)
"#;
const SPOTS_42: &[Spot] = &[
    spot(
        r#"litho layer"#,
        0,
        0,
        r#"Each litho layer is followed by an etch, then a clean."#,
    ),
    spot(
        r#"mask faceting"#,
        0,
        0,
        r#"Corners of the mask erode at an angle, which shifts the edge of the etched feature."#,
    ),
    spot(
        r#"LER"#,
        0,
        0,
        r#"Line-edge roughness in the mask is copied into the film."#,
    ),
    spot(
        r#"CD drift"#,
        0,
        0,
        r#"Critical-dimension drift: the etched width wanders from target."#,
    ),
    spot(
        r#"NAND       ▶ ~30% more word lines per generation"#,
        0,
        TO_EOL,
        r#"Per the cryo-etch article. More word lines mean more etch time per wafer."#,
    ),
];

const ART_43: &str = r#"# Avalanche ignition

  RF field ──▶ free electron e-  ──▶ speeds up
                      │
                      ▼ hits gas molecule
          molecule ──▶ ion + 2nd electron
                      │
                      ▼ both accelerate
          4 electrons ──▶ 8 ──▶ ... sustained plasma

  pressure 5-100 mTorr
    lower: too few molecules to hit
    higher: electrons lose energy before ionising
"#;
const SPOTS_43: &[Spot] = &[
    spot(
        r#"RF field"#,
        0,
        0,
        r#"The oscillating field pushes the light electrons far more than the heavy gas molecules."#,
    ),
    spot(
        r#"hits gas molecule"#,
        0,
        0,
        r#"An electron with enough energy ionises the molecule, freeing another electron."#,
    ),
    spot(
        r#"4 electrons"#,
        0,
        0,
        r#"Each collision multiplies the electrons until the loss rate balances the creation rate and the discharge sustains itself (textbook)."#,
    ),
    spot(
        r#"lower: too few molecules to hit"#,
        0,
        0,
        r#"Low pressure means electrons rarely meet a molecule."#,
    ),
    spot(
        r#"higher: electrons lose energy before ionising"#,
        0,
        0,
        r#"At higher pressure electrons collide too often to build up energy between collisions."#,
    ),
];

const ART_44: &str = r#"# Two ways to light the gas

  capacitive RIE             inductive ICP
  ┌────────────┐             ┌── coil (RF source) ──┐
  │ top plate  │             │  dielectric window   │
  │  ≈ plasma ≈│             │   ≈≈ plasma ≈≈       │
  │ wafer plate│ one RF      │  wafer + bias RF     │
  └────────────┘ drives both └──────────────────────┘
  density lower               ~1e11 /cm3, high density
  flux and energy tied        flux and energy separate

  ICP spec: up to 2500 W at 2.4 MHz; bias 13.56 MHz
"#;
const SPOTS_44: &[Spot] = &[
    spot(
        r#"capacitive RIE"#,
        0,
        0,
        r#"Two parallel plates driven by one RF supply, so ion flux and ion energy move together."#,
    ),
    spot(
        r#"inductive ICP"#,
        0,
        0,
        r#"A coil outside a dielectric window induces the field; a second RF on the wafer electrode sets ion energy."#,
    ),
    spot(
        r#"density lower"#,
        0,
        0,
        r#"Capacitive coupling gives a lower density plasma."#,
    ),
    spot(
        r#"~1e11 /cm3, high density"#,
        0,
        0,
        r#"The page's figure for a high-density plasma (textbook)."#,
    ),
    spot(
        r#"ICP spec: up to 2500 W at 2.4 MHz; bias 13.56 MHz"#,
        0,
        0,
        r#"From the tool spec and patent cited on the page."#,
    ),
];

const ART_45: &str = r#"# What can go wrong

  unstable ignition ──▶ first wafer in a lot differs
  arcing            ──▶ particles, damaged film
  impedance drift   ──▶ wafer-to-wafer variation

  hundreds of chambers must give the same etch
  ──▶ chamber matching: service + software

  Lam FY2025 revenue
    systems   ██████████████████████████████████ 62%
    services  ████████████████████ 38%
"#;
const SPOTS_45: &[Spot] = &[
    spot(
        r#"unstable ignition"#,
        0,
        0,
        r#"The discharge fails to start cleanly, so early wafers see different conditions."#,
    ),
    spot(
        r#"arcing"#,
        0,
        0,
        r#"Sudden discharges can throw particles onto the wafer."#,
    ),
    spot(
        r#"impedance drift"#,
        0,
        0,
        r#"Chamber walls change as they coat, which shifts the plasma and the etch."#,
    ),
    spot(
        r#"chamber matching"#,
        0,
        0,
        r#"Keeping hundreds of chambers etching identically is a major service and software problem."#,
    ),
    spot(
        r#"services  ████"#,
        0,
        TO_EOL,
        r#"Services were 38% of Lam's $18.44B FY2025 revenue (10-K)."#,
    ),
];

const ART_46: &str = r#"# Radicals attack from every side

  CF4 + e-  ──▶  CF3 + F + e-
                       │ radical (neutral)
        ╲   │   ╱  arrives from every angle
         ▼  ▼  ▼
   ████         ████       mask
   ▒▒▒░░░░░░░░░░░▒▒▒       film, etched sideways
   ▒▒░░░░░░░░░░░░░▒▒       isotropic: undercuts the mask
   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒       stop layer

  Si + 4F ──▶ SiF4 (gas, pumped away)
"#;
const SPOTS_46: &[Spot] = &[
    spot(
        r#"CF4 + e-"#,
        0,
        0,
        r#"An electron breaks a fluorocarbon molecule into radicals (textbook)."#,
    ),
    spot(
        r#"radical (neutral)"#,
        0,
        0,
        r#"Neutrals feel no electric field, so their direction is random."#,
    ),
    spot(
        r#"arrives from every angle"#,
        0,
        0,
        r#"Which is why radicals alone etch sideways as well as down."#,
    ),
    spot(
        r#"isotropic: undercuts the mask"#,
        0,
        0,
        r#"Etch under the mask edge. Ions are needed to make the profile vertical."#,
    ),
    spot(
        r#"SiF4 (gas, pumped away)"#,
        0,
        0,
        r#"The volatile product that carries silicon out of the chamber."#,
    ),
];

const ART_47: &str = r#"# What gas etches what (textbook)

  film                gas               volatile product
  oxide, nitride      CF4, C4F8         SiF4, CO
  poly-Si, fins       Cl2, HBr          SiCl4
  3D NAND stack       HF gas, cold      (PF3 catalyst)
                      wafer

  SiO2 + 4F  ──▶ SiF4 + O2      slow without ions
  Si + 2Cl2  ──▶ SiCl4
"#;
const SPOTS_47: &[Spot] = &[
    spot(
        r#"oxide, nitride"#,
        0,
        TO_EOL,
        r#"Fluorocarbons such as CF4 and C4F8 supply fluorine for oxide and nitride etch (textbook)."#,
    ),
    spot(
        r#"poly-Si, fins"#,
        0,
        TO_EOL,
        r#"Chlorine or HBr chemistries are used for polysilicon and fins (textbook)."#,
    ),
    spot(
        r#"3D NAND stack"#,
        0,
        TO_EOL,
        r#"The cryo-etch article cites HF gas at cold wafer temperature, with PF3 as a catalyst that raises the rate."#,
    ),
    spot(
        r#"SiO2 + 4F"#,
        0,
        0,
        r#"Slow without ion bombardment, because Si-O bonds are strong."#,
    ),
    spot(
        r#"Si + 2Cl2"#,
        0,
        0,
        r#"Chlorine forms volatile silicon tetrachloride."#,
    ),
];

const ART_48: &str = r#"# Ion-free etch releases nanosheets (GAA)

  before                      after lateral SiGe removal
  ┌──────────────┐            ┌──────────────┐
  │ Si   channel │            │ Si   channel │
  │ SiGe ░░░░░░░ │            │              │  gap
  │ Si   channel │            │ Si   channel │
  │ SiGe ░░░░░░░ │            │              │  gap
  │ Si   channel │            │ Si   channel │
  └──────────────┘            └──────────────┘
  radicals only: removes SiGe sideways, leaves Si
  IBM work: dry SiGe etch, roughly 150:1 selectivity over Si
"#;
const SPOTS_48: &[Spot] = &[
    spot(
        r#"before"#,
        0,
        0,
        r#"Alternating silicon and silicon-germanium layers, as grown."#,
    ),
    spot(
        r#"after lateral SiGe removal"#,
        0,
        0,
        r#"The SiGe is etched away sideways, leaving suspended silicon channels."#,
    ),
    spot(
        r#"radicals only"#,
        0,
        0,
        r#"Without ion bombardment the etch is isotropic and chemical, which is what is wanted here."#,
    ),
    spot(
        r#"IBM work: dry SiGe etch, roughly 150:1 selectivity over Si"#,
        0,
        0,
        r#"Reported by IBM for stacked gate-all-around nanosheet devices."#,
    ),
];

const ART_49: &str = r#"# Synergy: ions plus radicals

  etch rate
    radicals only   ██ slow
    ions only       ██ slow (sputter)
    both together   ████████████████████ fast

     ions ↓↓↓↓      radicals ≈ ≈
   ████         ████
   ▒▒▒▒         ▒▒▒▒       ions hit the floor head-on
   ▒▒▒▒         ▒▒▒▒       sidewalls see few ions
   ▒▒▒▒░░░░░░░░░▒▒▒▒
   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
"#;
const SPOTS_49: &[Spot] = &[
    spot(
        r#"radicals only"#,
        0,
        TO_EOL,
        r#"Slow on oxide because Si-O bonds are strong (textbook)."#,
    ),
    spot(
        r#"ions only"#,
        0,
        TO_EOL,
        r#"Pure sputtering is also slow and wears the mask."#,
    ),
    spot(
        r#"both together"#,
        0,
        TO_EOL,
        r#"The synergy: far faster than the sum of either alone (textbook)."#,
    ),
    spot(
        r#"ions ↓↓↓↓      radicals"#,
        0,
        0,
        r#"Ions arrive at near-normal incidence after crossing the sheath."#,
    ),
    spot(
        r#"ions hit the floor head-on"#,
        0,
        0,
        r#"Which breaks bonds on the floor and leaves the sidewalls alone."#,
    ),
];

const ART_50: &str = r#"# Two knobs

  source power ──▶ plasma density ──▶ ion FLUX    (how many)
  bias power   ──▶ sheath voltage ──▶ ion ENERGY  (how hard)
                   roughly 1 V per watt, geometry dependent

  bias up                       bias down
  ▲ straighter holes            ▼ better mask selectivity
  ▲ faster floor etch           ▼ less lattice damage
  ▼ more mask loss, damage      ▼ slower, less straight
"#;
const SPOTS_50: &[Spot] = &[
    spot(
        r#"source power"#,
        0,
        TO_EOL,
        r#"Sets how many ions arrive."#,
    ),
    spot(
        r#"bias power"#,
        0,
        TO_EOL,
        r#"Sets how hard they hit, via the sheath voltage."#,
    ),
    spot(
        r#"bias up"#,
        0,
        0,
        r#"More ion energy keeps holes straight and speeds the floor etch."#,
    ),
    spot(
        r#"bias down"#,
        0,
        0,
        r#"Lower energy spares the mask and the crystal lattice but is slower."#,
    ),
    spot(
        r#"▼ more mask loss, damage"#,
        0,
        0,
        r#"The cost of higher ion energy: worse selectivity to the mask and more lattice damage."#,
    ),
];

const ART_51: &str = r#"# Ions lose energy going down

  top      ↓↓↓↓  full energy, narrow angle
   │       ↓↓↓
   │        ↓↓   deflected by walls and charging
   │         ↓
  floor      ·   few ions arrive, etch slows

  fixes
    more bias    ▶ more energy at the floor
    pulsed bias  ▶ decouple energy from angle
    cryo cooling ▶ more neutrals adsorbed
    low-freq bias▶ higher energy, narrower angle
"#;
const SPOTS_51: &[Spot] = &[
    spot(
        r#"top      ↓↓↓↓"#,
        0,
        TO_EOL,
        r#"At the mouth ions still carry the sheath energy and a narrow angle."#,
    ),
    spot(
        r#"floor      ·"#,
        0,
        TO_EOL,
        r#"Few ions reach the floor with enough energy, so the etch rate falls with depth."#,
    ),
    spot(
        r#"more bias"#,
        0,
        TO_EOL,
        r#"More ion energy compensates for losses on the way down, at some cost in mask selectivity."#,
    ),
    spot(
        r#"pulsed bias"#,
        0,
        TO_EOL,
        r#"Pulsing helps decouple ion energy from angle distribution. Lam's Akara is described as using plasma pulsing."#,
    ),
    spot(
        r#"low-freq bias"#,
        0,
        TO_EOL,
        r#"A 2025 JVST paper describes low-frequency substrate bias as a way to raise ion energy and narrow angular spread."#,
    ),
];

const ART_52: &str = r#"# Film grows everywhere, ions remove it from the floor

     ions ↓↓↓↓   radicals ≈ ≈
   ████         ████
   ▒▒▒▒▓       ▓▒▒▒▒    ▓ = passivation film
   ▒▒▒▒▓       ▓▒▒▒▒      blocks radicals from the walls
   ▒▒▒▒▓░░░░░░░▓▒▒▒▒    ░ floor: film sputtered off,
   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒      fresh film etched

  CF-polymer from fluorocarbon gas (O2 oxide in Si etch)
"#;
const SPOTS_52: &[Spot] = &[
    spot(
        r#"▓ = passivation film"#,
        0,
        0,
        r#"Thin polymer or oxide film that deposits on all surfaces."#,
    ),
    spot(
        r#"blocks radicals from the walls"#,
        0,
        0,
        r#"The film shields the sidewall from neutral radical attack."#,
    ),
    spot(
        r#"░ floor: film sputtered off,"#,
        0,
        0,
        r#"Ions strike the floor directly and remove the film there, so etching continues downward."#,
    ),
    spot(
        r#"CF-polymer from fluorocarbon gas (O2 oxide in Si etch)"#,
        0,
        0,
        r#"Typical film sources (textbook)."#,
    ),
];

const ART_53: &str = r#"# Three outcomes

  too little          balanced            too much
  ▒▒▒▒░░░░▒▒▒▒        ▒▒▒▒░░░░▒▒▒▒        ▒▒▒▒▓░░▓▒▒▒▒   mouth pinched
  ▒▒░░░░░░░░▒▒        ▒▒▒▒░░░░▒▒▒▒        ▒▒▒▒▒░░▒▒▒▒▒
  ▒░░░░░░░░░░▒        ▒▒▒▒░░░░▒▒▒▒        ▒▒▒▒▒▒░▒▒▒▒▒
  ▒▒░░░░░░░░▒▒        ▒▒▒▒░░░░▒▒▒▒        ▒▒▒▒▒▒▒▒▒▒▒▒   etch stops
  bowing, undercut    vertical            taper, etch stop
"#;
const SPOTS_53: &[Spot] = &[
    spot(
        r#"too little"#,
        0,
        0,
        r#"Walls are attacked sideways: bowing and undercut."#,
    ),
    spot(
        r#"balanced"#,
        0,
        0,
        r#"Film grows as fast as radicals remove it from the walls: vertical profile."#,
    ),
    spot(
        r#"too much"#,
        0,
        0,
        r#"Polymer builds up, narrowing the hole (taper)."#,
    ),
    spot(
        r#"mouth pinched"#,
        0,
        0,
        r#"If polymer closes the mouth, the etch stops (an etch-stop failure)."#,
    ),
    spot(
        r#"bowing, undercut"#,
        0,
        0,
        r#"A 3D NAND patent notes insufficient sidewall passivation results in bowing and poor critical dimension control."#,
    ),
];

const ART_54: &str = r#"# Room temperature versus cryo

               room temp            cryo, 0 to -30 C
  sidewall     needs polymer        cold surface resists attack
  neutrals     bounce off           adsorb on the surface
  floor etch   slows with depth     faster
  polymer      lots, can clog       less needed

  TEL cryo etcher: 84% lower carbon than its first
  cryo run (TEL report in the cryo-etch article)
"#;
const SPOTS_54: &[Spot] = &[
    spot(
        r#"sidewall     needs polymer"#,
        0,
        TO_EOL,
        r#"At room temperature the walls need a protective film to survive."#,
    ),
    spot(
        r#"neutrals     bounce off"#,
        0,
        TO_EOL,
        r#"Cold wafers adsorb more neutral reactants instead."#,
    ),
    spot(
        r#"floor etch   slows with depth"#,
        0,
        TO_EOL,
        r#"Cryo etch speeds the floor etch, which matters in deep NAND holes."#,
    ),
    spot(
        r#"TEL cryo etcher: 84% lower carbon than its first"#,
        0,
        0,
        r#"From the cryo-etch article. Lower carbon matters for PFAS and greenhouse-gas pressure on fluorocarbon gases."#,
    ),
];

const ART_55: &str = r#"# After etch, three things to remove

  ████         ████     1 leftover mask or resist
  ▒▒▒▒▓       ▓▒▒▒▒     2 sidewall polymer (▓)
  ▒▒▒▒▓░░░░░░░▓▒▒▒▒     3 halogen residues (░ on the floor)
  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

  O2 plasma ash ──▶ wet clean ──▶ next step
  (textbook order)
"#;
const SPOTS_55: &[Spot] = &[
    spot(
        r#"1 leftover mask or resist"#,
        0,
        0,
        r#"Typically removed by oxygen plasma ashing (textbook)."#,
    ),
    spot(
        r#"2 sidewall polymer"#,
        0,
        0,
        r#"The passivation film that protected the walls during etch."#,
    ),
    spot(
        r#"3 halogen residues"#,
        0,
        0,
        r#"Chlorine or fluorine residues can corrode metal if left on the wafer."#,
    ),
    spot(
        r#"O2 plasma ash"#,
        0,
        0,
        r#"Oxygen plasma burns off organic resist and polymer (textbook)."#,
    ),
    spot(
        r#"wet clean"#,
        0,
        0,
        r#"Wet chemistries follow the ash step (textbook). See the CLEAN page."#,
    ),
];

const ART_56: &str = r#"# Etch + clean share of wafer-fab equipment (Yole)

  2022     ███████████████████████████ 27%
  H1 2024  ███████████████████ 19%

  etch + clean revenue 2023: down 16.7% (NAND capex downturn)

  every litho layer ──▶ etch ──▶ clean
  so the two are reported together
"#;
const SPOTS_56: &[Spot] = &[
    spot(
        r#"2022     ███"#,
        0,
        TO_EOL,
        r#"Yole Group: etch plus clean at 27% of wafer-fab equipment in 2022."#,
    ),
    spot(
        r#"H1 2024  ███"#,
        0,
        TO_EOL,
        r#"Etch plus clean fell to 19% of WFE in H1 2024, down from 27% in 2022 (Yole Group)."#,
    ),
    spot(
        r#"etch + clean revenue 2023: down 16.7% (NAND capex downturn)"#,
        0,
        0,
        r#"Yole Group figure, tied to the NAND capex downturn."#,
    ),
    spot(
        r#"every litho layer"#,
        0,
        0,
        r#"The reason market data lump etch and clean."#,
    ),
];

const ART_57: &str = r#"# Too little, too much

  too little strip            too much strip
  ┌──┐ ▓▓ ┌──┐                ┌──┐    ┌──┐
  │  │ ▓▓ │  │ residue        │  )    (  │ walls attacked
  │  │    │  │ ──▶ opens,     │  │    │  │ low-k damaged
  └──┘    └──┘     shorts      └──┘    └──┘

  10 um deep hole: clean chemistry must get in
  and byproducts must get out (transport problem)
"#;
const SPOTS_57: &[Spot] = &[
    spot(
        r#"too little strip"#,
        0,
        0,
        r#"Leftover polymer or particles cause opens and shorts in later layers."#,
    ),
    spot(
        r#"too much strip"#,
        0,
        0,
        r#"Aggressive strip can attack the sidewalls just carved or damage low-k dielectrics (textbook)."#,
    ),
    spot(
        r#"residue"#,
        0,
        0,
        r#"Residual material leaves defects in later layers."#,
    ),
    spot(
        r#"10 um deep hole"#,
        0,
        0,
        r#"Moving chemistry in and byproducts out of a 10 um deep hole is itself a hard transport problem."#,
    ),
];

const ART_58: &str = r#"# Gas path

   process gas in
        │
        ▼
  ┌─────────────── plenum ───────────────┐
  │                                      │
  └─┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┘
    ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼   thousands of holes
  ≈≈≈≈≈≈≈≈≈≈ plasma 5-100 mTorr ≈≈≈≈≈≈≈≈≈≈
  ═══════════════ 300 mm wafer ═══════════
  same gas at every point ──▶ same etch rate
"#;
const SPOTS_58: &[Spot] = &[
    spot(
        r#"plenum"#,
        0,
        0,
        r#"A gas reservoir above the holes that evens out pressure."#,
    ),
    spot(
        r#"thousands of holes"#,
        0,
        0,
        r#"Small holes turn the plenum into thousands of jets spread over the wafer."#,
    ),
    spot(
        r#"plasma 5-100 mTorr"#,
        0,
        0,
        r#"Typical pressure range for these etch chambers."#,
    ),
    spot(
        r#"300 mm wafer"#,
        0,
        0,
        r#"Uniform gas delivery sets uniform etch rate across the whole wafer (textbook)."#,
    ),
];

const ART_59: &str = r#"# Wear and tear

  new                 worn
  ○ ○ ○ ○ ○ ○         ◎ ◎ ○ ○ ◎ ◎    holes erode, flow changes
  ○ ○ ○ ○ ○ ○         ◎ ○ ○ ○ ○ ◎

  failure modes (textbook)
    hole erosion       flow changes
    flaking polymer    particles on the wafer
    edge vs centre     non-uniform etch

  materials: silicon, silicon carbide, yttria-coated or
  anodised aluminium ──▶ spares are recurring revenue
"#;
const SPOTS_59: &[Spot] = &[
    spot(r#"new"#, 0, 0, r#"Fresh holes at design size."#),
    spot(
        r#"hole erosion"#,
        0,
        0,
        r#"Plasma enlarges the holes over time, changing local gas flow."#,
    ),
    spot(
        r#"flaking polymer"#,
        0,
        0,
        r#"Polymer built up on the showerhead can flake onto the wafer as particles."#,
    ),
    spot(
        r#"edge vs centre"#,
        0,
        0,
        r#"Flow and plasma differ between the wafer's centre and edge."#,
    ),
    spot(
        r#"materials: silicon, silicon carbide, yttria-coated or"#,
        0,
        0,
        r#"Showerheads are consumable, which is why services include spares and upgrades."#,
    ),
];

const ART_60: &str = r#"# Lam Akara, as described

  direct-drive solid-state RF ─┐
                               ├──▶ Akara conductor etch
  plasma pulsing ──────────────┘

  targets
    gate-all-around logic
    advanced DRAM
    NAND

  installed base doubled in a year
  (secondary summary of the Q2 2026 call)
"#;
const SPOTS_60: &[Spot] = &[
    spot(
        r#"direct-drive solid-state RF"#,
        0,
        0,
        r#"RF delivery described for Akara in secondary coverage of Lam."#,
    ),
    spot(
        r#"plasma pulsing"#,
        0,
        0,
        r#"Pulsing helps control ion energy and angle."#,
    ),
    spot(
        r#"Akara conductor etch"#,
        0,
        0,
        r#"Lam's conductor etch platform."#,
    ),
    spot(
        r#"gate-all-around logic"#,
        0,
        0,
        r#"One of Akara's targeted applications."#,
    ),
    spot(
        r#"installed base doubled in a year"#,
        0,
        0,
        r#"From a secondary summary of Lam's Q2 2026 call, so treat with caution."#,
    ),
];

const ART_61: &str = r#"# What is in the plasma

  e-   electrons   light, fast: break molecules, ionise
  F    radicals    neutral, reactive: the chemical half
  Cl   radicals
  CF3+ ions        charged: carry energy to the wafer
  Ar+

  density ~1e11 /cm3 (ions and electrons)
  neutrals outnumber them by orders of magnitude
  ──▶ weakly ionised plasma (textbook)
"#;
const SPOTS_61: &[Spot] = &[
    spot(
        r#"e-   electrons"#,
        0,
        TO_EOL,
        r#"Light and fast, they do the dissociating and ionising."#,
    ),
    spot(
        r#"F    radicals"#,
        0,
        TO_EOL,
        r#"Neutral chemical reactants, such as fluorine."#,
    ),
    spot(
        r#"CF3+ ions"#,
        0,
        TO_EOL,
        r#"Charged species that carry energy to the wafer."#,
    ),
    spot(
        r#"density ~1e11 /cm3"#,
        0,
        0,
        r#"The page's figure for a high-density plasma."#,
    ),
    spot(
        r#"weakly ionised plasma (textbook)"#,
        0,
        0,
        r#"Neutral molecules and radicals still vastly outnumber ions and electrons."#,
    ),
];

const ART_62: &str = r#"# Plasma, sheath, wafer

  ≈≈≈≈≈≈≈ plasma (neutral overall) ≈≈≈≈≈≈≈
  ─ ─ ─ ─ ─ ─ ─ sheath edge ─ ─ ─ ─ ─ ─ ─ ─
     ↓    ↓    ↓    ↓    ↓    ions fall through
     ↓    ↓    ↓    ↓    ↓    a strong field
  ═══════════ wafer ═══════════════════════
  RF bias sets the sheath voltage = ion energy

  ions: narrow angle, vertical
  electrons: nearly isotropic ──▶ charge builds in deep holes
"#;
const SPOTS_62: &[Spot] = &[
    spot(
        r#"plasma (neutral overall)"#,
        0,
        0,
        r#"Equal numbers of positive ions and electrons."#,
    ),
    spot(
        r#"sheath edge"#,
        0,
        0,
        r#"Boundary of the thin region of strong field in front of the wafer."#,
    ),
    spot(
        r#"ions fall through"#,
        0,
        0,
        r#"The field accelerates them nearly perpendicular to the wafer."#,
    ),
    spot(
        r#"RF bias sets the sheath voltage = ion energy"#,
        0,
        0,
        r#"The bias power is the principal lever for ion energy."#,
    ),
    spot(
        r#"electrons: nearly isotropic"#,
        0,
        0,
        r#"Electrons arrive with near-thermal energy and isotropic angles, so deep holes can charge, which slows etch and can twist features (HAR etch literature)."#,
    ),
];

const ART_63: &str = r#"# Two independent dials

  source RF  ──▶ density ──▶ flux   (how many ions)
  bias RF    ──▶ sheath V ─▶ energy (how hard)

  RIE:  one RF sets both  ──▶ trade flux against energy
  ICP:  two RFs set each  ──▶ tune separately

  recipe: 30+ knobs interact
  AI tuned 33 of them once for a NAND recipe
  (cryo-etch article)
"#;
const SPOTS_63: &[Spot] = &[
    spot(
        r#"source RF"#,
        0,
        TO_EOL,
        r#"Controls plasma density, which sets the ion flux."#,
    ),
    spot(
        r#"bias RF"#,
        0,
        TO_EOL,
        r#"Controls the sheath voltage, which sets ion energy."#,
    ),
    spot(
        r#"RIE:  one RF sets both"#,
        0,
        0,
        r#"In a simple capacitive reactor you cannot change flux without changing energy."#,
    ),
    spot(
        r#"ICP:  two RFs set each"#,
        0,
        0,
        r#"Independent control is why ICP replaced RIE for demanding layers."#,
    ),
    spot(
        r#"AI tuned 33 of them once for a NAND recipe"#,
        0,
        0,
        r#"Cited in the cryo-etch article as an example of the recipe-space problem."#,
    ),
];

const ART_64: &str = r#"# ESC cross-section

  ions ↓↓↓↓↓ heat the wafer
  ═══════════════════ wafer
  ·· He ·· He ·· He ··   helium carries heat down
  ▓▓▓▓▓ ceramic + electrodes ▓▓▓▓▓   electrostatic force
  ▓▓▓▓▓ chiller channels ▓▓▓▓▓▓▓▓   coolant in and out

  without He cooling: wafer drifts hot
  ──▶ etch rate and profile change (textbook)
"#;
const SPOTS_64: &[Spot] = &[
    spot(
        r#"ions ↓↓↓↓↓ heat the wafer"#,
        0,
        0,
        r#"Ion bombardment dumps substantial power into the wafer (textbook)."#,
    ),
    spot(
        r#"He ·· He"#,
        0,
        0,
        r#"Helium flows behind the wafer to carry heat to the chuck."#,
    ),
    spot(
        r#"ceramic + electrodes"#,
        0,
        0,
        r#"Voltage on embedded electrodes clamps the wafer electrostatically, so it stays flat."#,
    ),
    spot(
        r#"chiller channels"#,
        0,
        0,
        r#"Coolant removes the heat that helium carries down."#,
    ),
    spot(
        r#"without He cooling: wafer drifts hot"#,
        0,
        0,
        r#"Etch rate and profile are temperature dependent (textbook)."#,
    ),
];

const ART_65: &str = r#"# Cryo chuck

  wafer temperature   0 to -30 C
  must be uniform across 300 mm
  while RF bias passes through the chuck
  without icing the wafer or condensing gas

  Lam vendor claims
    etch rate     ████████████████████████ >2x conventional
    energy/wafer  ██████████████ 40% lower
    installed     ~1,000 cryo chambers, 5 million wafers
"#;
const SPOTS_65: &[Spot] = &[
    spot(
        r#"wafer temperature   0 to -30 C"#,
        0,
        0,
        r#"Cryo etch range quoted in the cryo-etch article."#,
    ),
    spot(
        r#"must be uniform across 300 mm"#,
        0,
        0,
        r#"A hard engineering problem while RF power passes through the chuck."#,
    ),
    spot(
        r#"etch rate     ████"#,
        0,
        TO_EOL,
        r#"Vendor claim: more than twice the etch rate of conventional dielectric etch."#,
    ),
    spot(
        r#"energy/wafer  ████"#,
        0,
        TO_EOL,
        r#"Vendor claim: 40% lower energy per wafer."#,
    ),
    spot(
        r#"installed     ~1,000 cryo chambers, 5 million wafers"#,
        0,
        0,
        r#"Vendor claim: nearly 1,000 Lam cryo chambers installed in NAND fabs."#,
    ),
];

const ART_66: &str = r#"# What shows up in the data

  sticking / de-chuck errors ──▶ wafer breaks or shifts
  helium leak at the edge    ──▶ hot ring at the rim
  temperature non-uniform    ──▶ ring pattern in CD

   CD (nm)
   ^   ┌─────────┐
   |  ╱           ╲___ ring: hot edge etches faster
   └─────────────────────▶ radius
  (textbook)
"#;
const SPOTS_66: &[Spot] = &[
    spot(
        r#"sticking / de-chuck errors"#,
        0,
        0,
        r#"The wafer fails to release, or releases unevenly."#,
    ),
    spot(
        r#"helium leak at the edge"#,
        0,
        0,
        r#"Edge leaks starve cooling at the rim."#,
    ),
    spot(
        r#"temperature non-uniform"#,
        0,
        0,
        r#"Shows up as a ring pattern in critical dimension (textbook)."#,
    ),
    spot(
        r#"ring: hot edge etches faster"#,
        0,
        0,
        r#"Illustrative shape of an edge-ring CD error."#,
    ),
];

const ART_67: &str = r#"# What the cathode does

  RF bias 13.56 MHz ──▶ ┌──────────────┐
                        │  cathode     │ ──▶ sheath voltage
  chiller in ──▶        │  channels    │ ──▶ ion energy
  chiller out ◀──       │  ESC on top  │
                        └──────────────┘
  cryo: remove a lot of heat, hold 0 to -30 C
"#;
const SPOTS_67: &[Spot] = &[
    spot(
        r#"RF bias 13.56 MHz"#,
        0,
        0,
        r#"The bias frequency named on the page (textbook)."#,
    ),
    spot(
        r#"cathode     │"#,
        0,
        0,
        r#"The electrode under the chuck that couples RF into the plasma."#,
    ),
    spot(
        r#"sheath voltage"#,
        0,
        0,
        r#"The bias creates the sheath voltage, which sets ion energy."#,
    ),
    spot(
        r#"chiller in"#,
        0,
        0,
        r#"Coolant channels in the cathode hold wafer temperature."#,
    ),
    spot(
        r#"cryo: remove a lot of heat, hold 0 to -30 C"#,
        0,
        0,
        r#"The page quotes 0 to -30 C for cryo etch."#,
    ),
];

const ART_68: &str = r#"# Bias power versus the hole

  low bias    ions run out of energy half way down
  right bias  ions reach the floor
  too high    ions also sputter the mask away

  newer tools: pulsed + multi-frequency bias
    decouple ion energy from angle distribution

  focus ring around the wafer shapes the edge
    erodes with use ──▶ edge profile shifts (consumable)
"#;
const SPOTS_68: &[Spot] = &[
    spot(
        r#"low bias"#,
        0,
        0,
        r#"Ions lose energy and angle on the way down a deep hole."#,
    ),
    spot(
        r#"right bias"#,
        0,
        0,
        r#"Enough energy at the floor without destroying the mask."#,
    ),
    spot(
        r#"too high"#,
        0,
        0,
        r#"Too much ion energy sputters the mask."#,
    ),
    spot(
        r#"newer tools: pulsed + multi-frequency bias"#,
        0,
        0,
        r#"Used to decouple ion energy from angle distribution."#,
    ),
    spot(
        r#"focus ring around the wafer shapes the edge"#,
        0,
        0,
        r#"Ring erosion shifts edge profiles. It is a regular consumable (textbook)."#,
    ),
];

const ART_69: &str = r#"# Each generation asks for more

  word lines per generation    ▲ ~30% more  (cryo-etch article)
        │
        ▼
  deeper holes  ──▶ more bias power
                ──▶ more cooling
                ──▶ new cathode specs

  deep etch is used for NAND and for HBM (DRAM) stacks
"#;
const SPOTS_69: &[Spot] = &[
    spot(
        r#"word lines per generation"#,
        0,
        0,
        r#"About 30% more per generation, per the cryo-etch article cited on the page."#,
    ),
    spot(
        r#"deeper holes"#,
        0,
        0,
        r#"More tiers mean deeper holes, which need more ion energy at the floor."#,
    ),
    spot(
        r#"more cooling"#,
        0,
        0,
        r#"More power dumped into the wafer needs more heat removal."#,
    ),
    spot(
        r#"deep etch is used for NAND and for HBM (DRAM) stacks"#,
        0,
        0,
        r#"The page states both depend on deep etch."#,
    ),
];

const ART_70: &str = r#"# Vendor claims for Cryo 3.0

  etch rate     ████████████████████████ >2x conventional
  energy/wafer  ██████████████ -40%
  installed     ~1,000 chambers, 5 million wafers

  cold wafer, 0 to -30 C
    sidewall attack   ▼ falls
    adsorbed neutrals ▲ rise
    floor etch        ▲ faster
  (all vendor claims; not independently confirmed)
"#;
const SPOTS_70: &[Spot] = &[
    spot(
        r#"etch rate     ████"#,
        0,
        TO_EOL,
        r#"Vendor claim: more than 2x the etch rate of conventional dielectric etch."#,
    ),
    spot(
        r#"energy/wafer  ████"#,
        0,
        TO_EOL,
        r#"Vendor claim: 40% lower energy per wafer."#,
    ),
    spot(
        r#"installed     ~1,000 chambers, 5 million wafers"#,
        0,
        0,
        r#"Vendor claim: nearly 1,000 cryo chambers installed, covering 5 million wafers."#,
    ),
    spot(
        r#"sidewall attack   ▼ falls"#,
        0,
        0,
        r#"The cold surface suppresses attack on the walls."#,
    ),
    spot(
        r#"floor etch        ▲ faster"#,
        0,
        0,
        r#"More adsorbed neutrals at the floor speed the etch."#,
    ),
    spot(
        r#"(all vendor claims; not independently confirmed)"#,
        0,
        0,
        r#"A search of Lam's FY2026 10-K only confirms cryogenic etch is mentioned in general terms."#,
    ),
];

const ART_71: &str = r#"# Etch rate with depth (schematic)

  rate
   ^ ╲_______ conventional RIE: slows as holes deepen
   |   ╲ ______ cryo: holds up better
   └──────────────────────▶ aspect ratio
        ~70:1 today        100:1 much harder

  Lam end market: memory 42%
  TEL launched its first cryo etcher in 2023
"#;
const SPOTS_71: &[Spot] = &[
    spot(
        r#"conventional RIE: slows as holes deepen"#,
        0,
        0,
        r#"The cryo-etch article lists a falling etch rate with depth as a failure mode of conventional RIE."#,
    ),
    spot(
        r#"cryo: holds up better"#,
        0,
        0,
        r#"The claim behind cryo etch. The curve is schematic, not data."#,
    ),
    spot(
        r#"~70:1 today"#,
        0,
        0,
        r#"The page says NAND is approaching 70:1 today."#,
    ),
    spot(
        r#"100:1 much harder"#,
        0,
        0,
        r#"The page describes 100:1 as much harder."#,
    ),
    spot(
        r#"TEL launched its first cryo etcher in 2023"#,
        0,
        0,
        r#"Per the cryo-etch article."#,
    ),
];

const ART_72: &str = r#"# Memory cycles hit etch first

  NAND capex 2023   ▼▼▼ sharp drop
  etch + clean      ▼ -16.7% revenue (Yole)

  Lam end markets
    foundry        █████████████████████ 45%
    memory         ████████████████████ 42%
    logic, other   ██████ 13%

  no Cryo 3.0 detail confirmed beyond vendor claims
"#;
const SPOTS_72: &[Spot] = &[
    spot(
        r#"NAND capex 2023"#,
        0,
        0,
        r#"NAND capex dropped sharply in 2023."#,
    ),
    spot(
        r#"etch + clean      ▼ -16.7% revenue (Yole)"#,
        0,
        0,
        r#"Yole Group figure for 2023."#,
    ),
    spot(
        r#"foundry        ████"#,
        0,
        TO_EOL,
        r#"Lam FY2025 end-market mix: foundry 45%."#,
    ),
    spot(
        r#"memory         ████"#,
        0,
        TO_EOL,
        r#"Memory 42% of Lam FY2025 end markets."#,
    ),
    spot(r#"logic, other"#, 0, TO_EOL, r#"Logic and other 13%."#),
];

const ART_73: &str = r#"# Channel hole cross-section (not to scale)

     opening ~100 nm
  oxide  ▒▒▒▒▒▒▒▒    ▒▒▒▒▒▒▒▒
  nitr.  ░░░░░░░░    ░░░░░░░░    stack alternates oxide / nitride
  oxide  ▒▒▒▒▒▒▒▒    ▒▒▒▒▒▒▒▒    word-line pitch ~40 nm
  nitr.  ░░░░░░░░    ░░░░░░░░    ~10 um deep
  oxide  ▒▒▒▒▒▒▒▒    ▒▒▒▒▒▒▒▒    two-tier stack about 30 um
  nitr.  ░░░░░░░░    ░░░░░░░░
         (the gap in the middle is the hole)
  allowed deviation < 10 nm (<0.1% of depth)
"#;
const SPOTS_73: &[Spot] = &[
    spot(
        r#"opening ~100 nm"#,
        0,
        0,
        r#"Roughly 100 nm wide at the top, per the cryo-etch article."#,
    ),
    spot(
        r#"stack alternates oxide / nitride"#,
        0,
        0,
        r#"Alternating layers later become the word lines and insulators of the memory string."#,
    ),
    spot(
        r#"word-line pitch ~40 nm"#,
        0,
        0,
        r#"Z-pitch around 40 nm per the article."#,
    ),
    spot(
        r#"~10 um deep"#,
        0,
        0,
        r#"About 10 um deep for a single tier."#,
    ),
    spot(
        r#"two-tier stack about 30 um"#,
        0,
        0,
        r#"A tall two-tier stack is about 30 um."#,
    ),
    spot(
        r#"allowed deviation < 10 nm (<0.1% of depth)"#,
        0,
        0,
        r#"The tight tolerance that makes the etch so hard."#,
    ),
];

const ART_74: &str = r#"# Failure modes

  ideal     twist     bow       taper     stop short
  ▒▒░░▒▒   ▒▒░░▒▒   ▒▒░░▒▒   ▒░░░░▒   ▒▒░░▒▒
  ▒▒░░▒▒   ▒░░▒▒▒   ▒░░░░▒   ▒▒░░▒▒   ▒▒░░▒▒
  ▒▒░░▒▒   ▒▒▒░░▒   ▒░░░░▒   ▒▒▒░▒▒   ▒▒░░▒▒
  ▒▒░░▒▒   ▒▒░░▒▒   ▒▒░░▒▒   ▒▒▒▒▒▒   ▒▒▒▒▒▒

  tiny error at the top ──▶ big miss at the bottom
  causes: polymer at the mouth, ion energy and angle lost with depth
"#;
const SPOTS_74: &[Spot] = &[
    spot(
        r#"ideal"#,
        0,
        0,
        r#"A straight, round hole of constant diameter."#,
    ),
    spot(
        r#"twist"#,
        0,
        0,
        r#"The hole spirals off axis. Charging in the hole is one cause in the HAR etch literature."#,
    ),
    spot(
        r#"bow"#,
        0,
        0,
        r#"Walls bulge outward, often from insufficient sidewall passivation."#,
    ),
    spot(
        r#"taper"#,
        0,
        0,
        r#"Hole narrows with depth, often from too much polymer."#,
    ),
    spot(
        r#"stop short"#,
        0,
        0,
        r#"The etch stalls before reaching the bottom layer."#,
    ),
    spot(
        r#"tiny error at the top ──▶ big miss at the bottom"#,
        0,
        0,
        r#"Small deviations at the top become large misses at the bottom of a 10 um hole."#,
    ),
];

const ART_75: &str = r#"# More layers, more etch time

  generation   word lines
  N            ████████████████████ 1.0x
  N+1          ██████████████████████████ ~1.3x
  N+2          ██████████████████████████████████ ~1.7x
  (compounding the article's ~30% per generation)

  more word lines ──▶ more etch time per wafer
                  ──▶ more etch tools per bit

  vendors: Lam, TEL, Hitachi High-Tech
"#;
const SPOTS_75: &[Spot] = &[
    spot(r#"N            ███"#, 0, TO_EOL, r#"Reference generation."#),
    spot(
        r#"N+1          ███"#,
        0,
        TO_EOL,
        r#"About 30% more word lines (per the cryo-etch article)."#,
    ),
    spot(
        r#"N+2          ███"#,
        0,
        TO_EOL,
        r#"1.3 x 1.3 = 1.69, compounding the same rate (arithmetic)."#,
    ),
    spot(
        r#"more etch time per wafer"#,
        0,
        0,
        r#"Deeper stacks take longer to etch."#,
    ),
    spot(
        r#"vendors: Lam, TEL, Hitachi High-Tech"#,
        0,
        0,
        r#"Named as pitching cryo and high-aspect-ratio platforms to NAND makers."#,
    ),
];

const ART_76: &str = r#"# Aspect ratio = depth / width

  width 100 nm
   ┌┐
   ││
   ││  depth 7 um  ──▶ 70:1  (approaching today)
   ││
   ││  depth 10 um ──▶ 100:1 (much harder)
   ││
   └┘

  70:1  ███████████████████████████████████
  100:1 ██████████████████████████████████████████████████
  (10 um / 100 nm = 100: my arithmetic)
"#;
const SPOTS_76: &[Spot] = &[
    spot(
        r#"depth 7 um"#,
        0,
        0,
        r#"70:1 at a 100 nm width means 7 um deep (arithmetic)."#,
    ),
    spot(
        r#"depth 10 um"#,
        0,
        0,
        r#"10 um deep at 100 nm wide is 100:1 (arithmetic)."#,
    ),
    spot(
        r#"70:1  ████"#,
        0,
        TO_EOL,
        r#"The page says NAND is approaching 70:1 today."#,
    ),
    spot(
        r#"100:1 ████"#,
        0,
        TO_EOL,
        r#"The page describes 100:1 as much harder."#,
    ),
    spot(
        r#"(10 um / 100 nm = 100: my arithmetic)"#,
        0,
        0,
        r#"The article's 10 um and 100 nm figures are roughly current to next-generation, not identical limits."#,
    ),
];

const ART_77: &str = r#"# Four things fight the etch as it deepens

  ions         ↓ lose energy + angle on the way down
  neutrals     ↓ diffuse down slowly (Knudsen transport)
  byproducts   ↑ must diffuse up and out
  mask         erodes the whole time
  charging     deflects ions off axis

  30+ recipe knobs interact
  ──▶ rate falls as the hole deepens
"#;
const SPOTS_77: &[Spot] = &[
    spot(
        r#"ions         ↓"#,
        0,
        0,
        r#"Ions hit walls and lose energy and angle, so flux at the floor falls."#,
    ),
    spot(
        r#"neutrals     ↓"#,
        0,
        0,
        r#"Reactants must diffuse down a long narrow channel (Knudsen transport, textbook)."#,
    ),
    spot(
        r#"byproducts   ↑"#,
        0,
        0,
        r#"Volatile products must find their way back out."#,
    ),
    spot(
        r#"mask         erodes the whole time"#,
        0,
        0,
        r#"The longer the etch, the more mask is lost."#,
    ),
    spot(
        r#"charging     deflects ions off axis"#,
        0,
        0,
        r#"Positive charge builds in deep holes because electrons do not reach the floor (HAR etch literature)."#,
    ),
];

const ART_78: &str = r#"# Responses

  problem: etch slows and drifts at depth
     │
     ├── cryo etch            cold wafer, more neutrals
     ├── two-tier stacking    etch 2 shorter holes (~30 um stack)
     ├── pulsed bias          control ion energy and angle
     └── AI recipe tuning     33 knobs tuned once

  result: new aspect-ratio step ──▶ new etch tool purchases
"#;
const SPOTS_78: &[Spot] = &[
    spot(
        r#"cryo etch"#,
        0,
        0,
        r#"Cold wafer, less sidewall attack, faster floor etch."#,
    ),
    spot(
        r#"two-tier stacking"#,
        0,
        0,
        r#"String stacking in two tiers keeps each etched hole shorter. The article cites a stack of about 30 um."#,
    ),
    spot(
        r#"pulsed bias"#,
        0,
        0,
        r#"Helps decouple ion energy from angle."#,
    ),
    spot(
        r#"AI recipe tuning"#,
        0,
        0,
        r#"The article cites AI tuning 33 of 30+ knobs for a NAND recipe."#,
    ),
    spot(
        r#"new aspect-ratio step ──▶ new etch tool purchases"#,
        0,
        0,
        r#"The investor takeaway on the page."#,
    ),
];

const ART_79: &str = r#"# One ALE cycle

  1 modify      Cl2 ──▶ chlorine adsorbs on top layer only
      Cl Cl Cl Cl Cl Cl
      Si Si Si Si Si Si     self-limiting: stops when covered
      Si Si Si Si Si Si
  2 remove      low-energy Ar+ ──▶ only the Cl-Si layer leaves
      Si Si Si Si Si Si     bulk silicon below untouched
      Si Si Si Si Si Si
  repeat: fixed thin amount per cycle
"#;
const SPOTS_79: &[Spot] = &[
    spot(
        r#"1 modify"#,
        0,
        0,
        r#"Chlorine adsorbs on the top silicon layer. The reaction stops when the surface is covered."#,
    ),
    spot(
        r#"self-limiting: stops when covered"#,
        0,
        0,
        r#"The step cannot go deeper than one modified layer."#,
    ),
    spot(
        r#"2 remove"#,
        0,
        0,
        r#"Low-energy argon ions remove only the modified layer, because their energy is below the sputter threshold of bulk silicon."#,
    ),
    spot(
        r#"bulk silicon below untouched"#,
        0,
        0,
        r#"This is why ALE has atomic-scale control."#,
    ),
    spot(
        r#"repeat: fixed thin amount per cycle"#,
        0,
        0,
        r#"Each cycle removes a fixed thin amount."#,
    ),
];

const ART_80: &str = r#"# Removal per cycle (from the page's sources)

  Si, Cl2 + 50 eV Ar+    0.172 Si atoms per ion
                         (molecular-dynamics yield)
  SiO2, C4F8 / Ar+       ███████████████████ 1.9 A per cycle
  GaN/AlGaN              ████████████████ 1.63 A per cycle
                         (not silicon)

  1 angstrom = 0.1 nm: each cycle is about two atom layers or less
"#;
const SPOTS_80: &[Spot] = &[
    spot(
        r#"Si, Cl2 + 50 eV Ar+"#,
        0,
        0,
        r#"A molecular-dynamics yield of 0.172 Si atoms per ion, as quoted on the page."#,
    ),
    spot(
        r#"SiO2, C4F8 / Ar+"#,
        0,
        TO_EOL,
        r#"1.9 angstroms removed per cycle."#,
    ),
    spot(
        r#"GaN/AlGaN"#,
        0,
        TO_EOL,
        r#"1.63 angstroms per cycle. This is a different material from silicon."#,
    ),
    spot(
        r#"1 angstrom = 0.1 nm"#,
        0,
        0,
        r#"So a cycle removes well under a nanometre."#,
    ),
];

const ART_81: &str = r#"# ALE in a gate-all-around stack

  Si    ═══════  channel
  SiGe  ░░░░░░░  sacrificial, removed laterally
  Si    ═══════  channel
  SiGe  ░░░░░░░
  Si    ═══════  channel

  inner spacer cavity: etch SiGe sideways, stop on Si
  IBM: dry SiGe etch, ~150:1 selectivity over Si
  2025 study: gas etch gave highest selectivity,
              less nanosheet damage than ICP or remote plasma

  trade-off: slow ──▶ only thin, critical steps
"#;
const SPOTS_81: &[Spot] = &[
    spot(
        r#"Si    ═══════  channel"#,
        0,
        0,
        r#"Silicon channels that must survive."#,
    ),
    spot(
        r#"SiGe  ░░░░░░░  sacrificial"#,
        0,
        0,
        r#"Silicon-germanium layers removed laterally to release the channels."#,
    ),
    spot(
        r#"inner spacer cavity"#,
        0,
        0,
        r#"Lateral selective SiGe removal builds the inner spacer cavity."#,
    ),
    spot(
        r#"IBM: dry SiGe etch, ~150:1 selectivity over Si"#,
        0,
        0,
        r#"Roughly 150:1 selectivity reported by IBM for stacked GAA nanosheets."#,
    ),
    spot(
        r#"2025 study: gas etch gave highest selectivity,"#,
        0,
        0,
        r#"The study reports gas etching gave the highest SiGe selectivity with less nanosheet damage than ICP or remote plasma."#,
    ),
    spot(
        r#"trade-off: slow"#,
        0,
        0,
        r#"ALE is slow, so it is used only on thin critical steps (textbook)."#,
    ),
];

const ART_82: &str = r#"# Lam FY2025 revenue by region (% of $18.44B)

  China          ██████████████████████████████████ 34%
  Korea          ██████████████████████ 22%
  Taiwan         ███████████████████ 19%
  Japan          ██████████ 10%
  United States  ███████ 7%
  SE Asia        █████ 5%
  Europe         ███ 3%

  tighter export controls ──▶ up to a third of revenue at risk
  (textbook inference, not a filing quote)
"#;
const SPOTS_82: &[Spot] = &[
    spot(
        r#"China          ████"#,
        0,
        TO_EOL,
        r#"34% of $18.44B in FY2025, per Lam's 10-K."#,
    ),
    spot(
        r#"Korea          ████"#,
        0,
        TO_EOL,
        r#"Korea was Lam's second-largest region at 22% of FY2025 revenue."#,
    ),
    spot(
        r#"Taiwan         ████"#,
        0,
        TO_EOL,
        r#"Taiwan was the third-largest region at 19% of FY2025 revenue."#,
    ),
    spot(
        r#"Japan          ████"#,
        0,
        TO_EOL,
        r#"Japan was 10% of Lam's FY2025 revenue."#,
    ),
    spot(
        r#"tighter export controls"#,
        0,
        0,
        r#"A tightening could remove about a third of revenue quickly, a loosening add it back (textbook inference, not a filing quote)."#,
    ),
];

const ART_83: &str = r#"# Cushions inside the mix

  revenue type
    systems   ██████████████████████████████████ 62%
    services  ████████████████████ 38%   stickier, recurring

  end market
    foundry   █████████████████████████ 45%
    memory    ███████████████████████ 42%
    logic etc ███████ 13%

  China buyers: memory and foundry, domestic mature-node capacity
"#;
const SPOTS_83: &[Spot] = &[
    spot(
        r#"systems   ████"#,
        0,
        TO_EOL,
        r#"Systems were 62% of FY2025 revenue."#,
    ),
    spot(
        r#"services  ████"#,
        0,
        TO_EOL,
        r#"Services (spares, upgrades) were 38%, and are stickier than new tool sales."#,
    ),
    spot(
        r#"foundry   ████"#,
        0,
        TO_EOL,
        r#"Foundry 45% of end markets."#,
    ),
    spot(
        r#"memory    ████"#,
        0,
        TO_EOL,
        r#"Memory was 42% of end markets, so Lam also trades as a memory-capex proxy."#,
    ),
    spot(
        r#"China buyers: memory and foundry, domestic mature-node capacity"#,
        0,
        0,
        r#"Chinese makers pursuing domestic capacity at mature nodes."#,
    ),
];

const ART_84: &str = r#"# What to check next

  FY2025 China share    34%   (10-K, period ended Jun 2025)
  FY2026 China share    ?     check the FY2026 10-K
                              (period ended Jun 2026)

  rising threat: domestic Chinese etch makers
  (textbook, not verified here)
"#;
const SPOTS_84: &[Spot] = &[
    spot(
        r#"FY2025 China share"#,
        0,
        TO_EOL,
        r#"34%, from Lam's FY2025 10-K."#,
    ),
    spot(
        r#"FY2026 China share"#,
        0,
        TO_EOL,
        r#"Not obtained. The FY2026 10-K is filed and holds the answer."#,
    ),
    spot(
        r#"rising threat: domestic Chinese etch makers"#,
        0,
        0,
        r#"Chinese customers are being pushed toward local tools (textbook, not verified here)."#,
    ),
];

const ART_85: &str = r#"# WFE shares (Yole Group)

  Patterning 24e    ██████████████████████████████ 29%
  Etch+clean 22     ████████████████████████████ 27%
  Deposition 24e    ██████████████████████████ 25%
  Etch+clean H1-24  ███████████████████ 19%

  etch + clean revenue 2023: -16.7%
  (patterning = lithography)
"#;
const SPOTS_85: &[Spot] = &[
    spot(
        r#"Patterning 24e"#,
        0,
        TO_EOL,
        r#"Lithography at 29% of WFE in 2024e."#,
    ),
    spot(
        r#"Etch+clean 22"#,
        0,
        TO_EOL,
        r#"Yole Group: etch plus clean was 27% of wafer-fab equipment in 2022."#,
    ),
    spot(
        r#"Deposition 24e"#,
        0,
        TO_EOL,
        r#"Deposition was 25% of WFE in 2024e, per Yole Group."#,
    ),
    spot(
        r#"Etch+clean H1-24"#,
        0,
        TO_EOL,
        r#"Etch plus clean fell to 19% of WFE in H1 2024, down from 27% in 2022 (Yole Group)."#,
    ),
    spot(
        r#"etch + clean revenue 2023: -16.7%"#,
        0,
        0,
        r#"Fell as the NAND capex downturn bit."#,
    ),
];

const ART_86: &str = r#"# Why 27% became 19%

  numerator ▼   NAND spending fell
  denominator ▲ lithography and deposition grew faster

  etch + clean  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  smaller slice
                of a bigger pie

  definitions differ across analysts
  2024 WFE stable, then a 2025 surge (page note)
"#;
const SPOTS_86: &[Spot] = &[
    spot(
        r#"numerator ▼"#,
        0,
        0,
        r#"Lower NAND spending cut etch plus clean revenue."#,
    ),
    spot(
        r#"denominator ▲"#,
        0,
        0,
        r#"Lithography and deposition share rose in 2024, so the whole pie shifted."#,
    ),
    spot(
        r#"definitions differ across analysts"#,
        0,
        0,
        r#"Etch and clean boundaries vary between market trackers."#,
    ),
    spot(
        r#"2024 WFE stable, then a 2025 surge (page note)"#,
        0,
        0,
        r#"As noted on the page."#,
    ),
];

const ART_87: &str = r#"# Memory capex cycle

  memory capex  ▼ ──▶ etch orders ▼ first (levered to layer count)
  memory capex  ▲ ──▶ etch orders ▲ first (deep-hole tools bottleneck)

  LRCX end markets
    memory 42%   ◀── why it trades as a memory-capex proxy
    also an AI proxy via foundry (45%)

  (textbook reasoning)
"#;
const SPOTS_87: &[Spot] = &[
    spot(
        r#"memory capex  ▼"#,
        0,
        0,
        r#"Etch is heavily levered to NAND and DRAM layer count."#,
    ),
    spot(
        r#"memory capex  ▲"#,
        0,
        0,
        r#"Etch typically rebounds early because deep-hole etch tools bottleneck each wafer (textbook)."#,
    ),
    spot(
        r#"memory 42%"#,
        0,
        0,
        r#"Lam's FY2025 memory share of end markets."#,
    ),
    spot(
        r#"also an AI proxy via foundry (45%)"#,
        0,
        0,
        r#"Foundry was 45% of FY2025 end markets."#,
    ),
];

const ART_88: &str = r#"# TEL in etch

  2023   first cryogenic etcher launched
  later  84% lower carbon than its first cryo run
         (relevant to PFAS and greenhouse-gas pressure)

  strongest challenger to Lam in memory
  also dominant in coater/developers paired with EUV
"#;
const SPOTS_88: &[Spot] = &[
    spot(
        r#"2023   first cryogenic etcher launched"#,
        0,
        0,
        r#"Per the cryo-etch article."#,
    ),
    spot(
        r#"later  84% lower carbon"#,
        0,
        0,
        r#"Reported in the article against TEL's first cryo run."#,
    ),
    spot(
        r#"strongest challenger to Lam in memory"#,
        0,
        0,
        r#"TEL is the number two etch player."#,
    ),
    spot(
        r#"also dominant in coater/developers"#,
        0,
        0,
        r#"TEL sells both ends of the litho-etch loop."#,
    ),
];

const ART_89: &str = r#"# Etch revenue share (secondary reports)

  Lam + Applied  ██████████████████████████████ ~60%
  TEL            ██████████ ~20%
  others         ██████████ ~20%

  another report: top three ~90%
  definitions differ; no primary split is public
"#;
const SPOTS_89: &[Spot] = &[
    spot(
        r#"Lam + Applied"#,
        0,
        TO_EOL,
        r#"About 60% of etch revenue, per secondary reports."#,
    ),
    spot(
        r#"TEL            ████"#,
        0,
        TO_EOL,
        r#"About 20%, per secondary reports."#,
    ),
    spot(
        r#"others"#,
        0,
        TO_EOL,
        r#"What remains, derived (arithmetic)."#,
    ),
    spot(
        r#"another report: top three ~90%"#,
        0,
        0,
        r#"A different report puts the top three at about 90%."#,
    ),
    spot(
        r#"definitions differ; no primary split is public"#,
        0,
        0,
        r#"Treat all share figures as estimates."#,
    ),
];

const ART_90: &str = r#"# Who leads where

  NAND channel hole etch   Lam vs TEL (cryo)
  conductor etch           Applied Materials leads
  selective removal        Applied Materials
  deposition               Applied: bigger than in etch
  other etch               Hitachi High-Tech

  risks: Japan export policy, yen, NAND capex cycle
"#;
const SPOTS_90: &[Spot] = &[
    spot(
        r#"NAND channel hole etch"#,
        0,
        0,
        r#"The contest that decides who captures the biggest cryo volumes."#,
    ),
    spot(
        r#"conductor etch"#,
        0,
        0,
        r#"Applied leads here per the page."#,
    ),
    spot(
        r#"selective removal"#,
        0,
        0,
        r#"Applied Materials is strong here too."#,
    ),
    spot(
        r#"deposition"#,
        0,
        0,
        r#"Applied is bigger in deposition than etch."#,
    ),
    spot(
        r#"other etch"#,
        0,
        0,
        r#"Hitachi High-Tech is a further etch supplier."#,
    ),
    spot(
        r#"risks: Japan export policy, yen, NAND capex cycle"#,
        0,
        0,
        r#"Listed as risks (textbook)."#,
    ),
];

const ART_91: &str = r#"# Lam FY2025, $18.44B

  type        systems 62%  █████████████████████████████
              services 38% ██████████████████
  end market  foundry 45%  ██████████████████████
              memory 42%   █████████████████████
              logic etc 13%██████
  region      China 34%  Korea 22%  Taiwan 19%
"#;
const SPOTS_91: &[Spot] = &[
    spot(
        r#"type        systems 62%"#,
        0,
        TO_EOL,
        r#"Systems revenue share in FY2025."#,
    ),
    spot(r#"services 38%"#, 0, TO_EOL, r#"Services share in FY2025."#),
    spot(
        r#"end market  foundry 45%"#,
        0,
        TO_EOL,
        r#"Foundry share of end markets."#,
    ),
    spot(
        r#"memory 42%"#,
        0,
        TO_EOL,
        r#"Memory share of end markets."#,
    ),
    spot(
        r#"region      China 34%"#,
        0,
        TO_EOL,
        r#"Regional mix led by China, then Korea and Taiwan."#,
    ),
];

const ART_92: &str = r#"# Two pillars

  CRYO 3.0                         AKARA
  dielectric etch                  conductor etch
  3D NAND deep holes               GAA logic, advanced DRAM
  >2x etch rate (claim)            direct-drive solid-state RF
  -40% energy/wafer (claim)        plasma pulsing

  Akara roadmap (launch material)
    6F2 DRAM and 3D NAND ──▶ extendible to 4F2 DRAM, CFET, 3D DRAM
  Q2 2026 call (secondary): installed base doubled in a year
"#;
const SPOTS_92: &[Spot] = &[
    spot(
        r#"CRYO 3.0"#,
        0,
        0,
        r#"Third-generation cryogenic dielectric etch for the deepest NAND holes."#,
    ),
    spot(
        r#">2x etch rate (claim)"#,
        0,
        0,
        r#"Vendor claim, not independently confirmed."#,
    ),
    spot(
        r#"AKARA"#,
        0,
        0,
        r#"Conductor etch platform for gate-all-around logic and advanced DRAM."#,
    ),
    spot(
        r#"direct-drive solid-state RF"#,
        0,
        0,
        r#"RF delivery described for Akara."#,
    ),
    spot(
        r#"6F2 DRAM and 3D NAND"#,
        0,
        0,
        r#"Lam's launch material says Akara scales to these, and is extendible to 4F2 DRAM, CFET and 3D DRAM."#,
    ),
    spot(
        r#"Q2 2026 call (secondary): installed base doubled in a year"#,
        0,
        0,
        r#"From a secondary summary, so treat with caution."#,
    ),
];

const ART_93: &str = r#"# What can hurt LRCX

  NAND capex swings     ──▶ cryo orders
  China export controls ──▶ 34% of FY2025 revenue
  TEL, AMAT competition ──▶ share in memory and conductor etch

  current numbers: FY2026 10-K (period ended Jun 2026)
"#;
const SPOTS_93: &[Spot] = &[
    spot(
        r#"NAND capex swings"#,
        0,
        0,
        r#"Cryo etch is memory-capex dependent."#,
    ),
    spot(
        r#"China export controls"#,
        0,
        0,
        r#"China was 34% of FY2025 revenue."#,
    ),
    spot(
        r#"TEL, AMAT competition"#,
        0,
        0,
        r#"TEL challenges in memory, Applied in conductor etch."#,
    ),
    spot(
        r#"current numbers: FY2026 10-K"#,
        0,
        0,
        r#"The FY2026 10-K is filed and holds current figures."#,
    ),
];

const ART_94: &str = r#"# Arc chamber

   gas in ──▶ ┌───────────────────────┐
              │  hot filament  ~~~~   │
              │  ≈≈ plasma ≈≈≈≈≈≈≈≈   │──▶ slit ──▶ extraction
              │  e- strip electrons   │
              │  from the gas         │
              └───────────────────────┘
  molecule + e-  ──▶  ion+ + 2 e-
  a mix of ions comes out; the mass filter picks one (next stage)
"#;
const SPOTS_94: &[Spot] = &[
    spot(
        r#"gas in"#,
        0,
        0,
        r#"A low-pressure gas or vapour that carries the dopant."#,
    ),
    spot(
        r#"hot filament"#,
        0,
        0,
        r#"A hot filament (or RF) strikes the plasma."#,
    ),
    spot(
        r#"e- strip electrons"#,
        0,
        0,
        r#"Collisions in the plasma strip electrons from dopant-bearing molecules, making ions (textbook)."#,
    ),
    spot(
        r#"slit"#,
        0,
        0,
        r#"Ions leave the arc chamber through a slit, pulled by the extraction electrodes."#,
    ),
    spot(
        r#"a mix of ions comes out; the mass filter picks one (next stage)"#,
        0,
        0,
        r#"The source makes several species, so the analyser magnet selects the wanted one."#,
    ),
];

const ART_95: &str = r#"# Feed gas, dopant

  BF3   ──▶  boron     B, B+, BF2+ ...        p-type
  AsH3  ──▶  arsenic   As+                    n-type, toxic gas
  PH3   ──▶  phosphorus P+                    n-type, toxic gas

  AsH3 and PH3: tight safety rules (textbook, unsourced)
  switching dopant ──▶ retune source and analyser
  cross-contamination between species is a yield risk
"#;
const SPOTS_95: &[Spot] = &[
    spot(
        r#"BF3   ──▶"#,
        0,
        TO_EOL,
        r#"Boron trifluoride feeds boron implants. The source makes several boron-bearing ions such as B+ and BF2+."#,
    ),
    spot(
        r#"AsH3  ──▶"#,
        0,
        TO_EOL,
        r#"Arsine feeds arsenic implants. It is toxic."#,
    ),
    spot(
        r#"PH3   ──▶"#,
        0,
        TO_EOL,
        r#"Phosphine feeds phosphorus implants. It is toxic."#,
    ),
    spot(
        r#"AsH3 and PH3: tight safety rules"#,
        0,
        0,
        r#"Handled under tight safety rules (textbook, unsourced)."#,
    ),
    spot(
        r#"switching dopant"#,
        0,
        0,
        r#"Changing species means retuning the source and analyser."#,
    ),
];

const ART_96: &str = r#"# Source is the throughput limit

  beam current from the source
    medium current   █ ~1 uA to 5 mA
    high current     ██████████████████████ up to ~25-30 mA

  source life
    erodes + coats ──▶ clean ──▶ replace ──▶ downtime
    (consumable, a maintenance interval: textbook)

  SiC: heavy dopants + hot wafers add source challenges
"#;
const SPOTS_96: &[Spot] = &[
    spot(
        r#"medium current   █"#,
        0,
        TO_EOL,
        r#"Medium-current tools run roughly 1 uA to 5 mA (Wikipedia gives 10 uA to 2 mA)."#,
    ),
    spot(
        r#"high current     ███"#,
        0,
        TO_EOL,
        r#"High-current implants need up to roughly 25-30 mA of beam."#,
    ),
    spot(
        r#"erodes + coats"#,
        0,
        0,
        r#"Sources erode and coat with deposits (textbook)."#,
    ),
    spot(
        r#"downtime"#,
        0,
        0,
        r#"Fabs weigh tool uptime heavily when choosing between Applied Materials and Axcelis."#,
    ),
    spot(
        r#"SiC: heavy dopants + hot wafers add source challenges"#,
        0,
        0,
        r#"The niche Axcelis emphasises."#,
    ),
];

const ART_97: &str = r#"# Extraction

  arc chamber        electrodes
  ┌─────────┐       ║   ║   ║
  │  + + +  │ slit  ║   ║   ║
  │  + + +  │══▶═══ ║   ║   ║ ═══▶  beam to analyser
  │  + + +  │       ║   ║   ║
  └─────────┘       ║   ║   ║
   +  at source      −  extraction
   voltage of roughly kilovolts gives the first energy
"#;
const SPOTS_97: &[Spot] = &[
    spot(
        r#"arc chamber"#,
        0,
        0,
        r#"Where the plasma makes the ions."#,
    ),
    spot(
        r#"slit"#,
        0,
        0,
        r#"Ions are pulled out through a narrow slit."#,
    ),
    spot(
        r#"electrodes"#,
        0,
        0,
        r#"A voltage of roughly kilovolts between source and extraction electrode accelerates ions out."#,
    ),
    spot(
        r#"beam to analyser"#,
        0,
        0,
        r#"The beam next enters the analyser magnet."#,
    ),
    spot(
        r#"voltage of roughly kilovolts gives the first energy"#,
        0,
        0,
        r#"Page figure; the mechanism is textbook."#,
    ),
];

const ART_98: &str = r#"# Extract fast, slow down late

  low energy all the way         extract high, decelerate
  ions repel each other          tight beam in transit
      ·  ·   ·                   ─────────────┐
    ·   ·  ·   ·  spreads                      ▼ decel lens
      ·  ·   ·                       ──▶ low energy at the wafer
  ──▶ beam blows up              (high-current tools, 0.1-100 keV)
"#;
const SPOTS_98: &[Spot] = &[
    spot(
        r#"low energy all the way"#,
        0,
        0,
        r#"Like charges repel, so a dense low-energy beam spreads out (space charge)."#,
    ),
    spot(
        r#"extract high, decelerate"#,
        0,
        0,
        r#"A tight high-energy beam travels the beamline, then slows down before the wafer."#,
    ),
    spot(
        r#"decel lens"#,
        0,
        0,
        r#"Deceleration after extraction gives low wafer energy without the space-charge blow-up."#,
    ),
    spot(
        r#"(high-current tools, 0.1-100 keV)"#,
        0,
        0,
        r#"The class that uses deceleration most, with doses of 1e14 to 1e17 per cm2."#,
    ),
];

const ART_99: &str = r#"# What interrupts the beam

  arc / glitch at an electrode ──▶ beam drops out
                                  ──▶ dose error on that wafer
  deposits on electrodes       ──▶ clean ──▶ downtime

  beam current
   ^  ───┐   ┌────┐  ┌───
   |     └───┘    └──┘      glitches
   └──────────────────────▶ time
"#;
const SPOTS_99: &[Spot] = &[
    spot(
        r#"arc / glitch at an electrode"#,
        0,
        0,
        r#"Arcs and glitches interrupt the beam."#,
    ),
    spot(
        r#"dose error on that wafer"#,
        0,
        0,
        r#"An interrupted beam delivers less dose than intended unless the dose loop compensates."#,
    ),
    spot(
        r#"deposits on electrodes"#,
        0,
        0,
        r#"Deposits need cleaning, which takes the tool offline."#,
    ),
    spot(
        r#"glitches"#,
        0,
        0,
        r#"Each dropout shows as a dip in beam current."#,
    ),
];

const ART_100: &str = r#"# 90 degree magnet

             ┌── magnet B ──┐
  beam in ══▶│  light  ╲    │
             │  wanted  ╲═══│══▶ slit ══▶ beam out
             │  heavy    ╲  │
             └──────────────┘
     light ions bend too much, heavy ions too little
     wrong radius ──▶ hit the slit wall and stop

  r = m v / (q B)
"#;
const SPOTS_100: &[Spot] = &[
    spot(
        r#"magnet B"#,
        0,
        0,
        r#"A magnetic field perpendicular to the beam bends ions along arcs."#,
    ),
    spot(
        r#"light  ╲"#,
        0,
        0,
        r#"Lighter ions have a smaller radius and strike the inside of the slit."#,
    ),
    spot(
        r#"wanted  ╲"#,
        0,
        0,
        r#"Only the chosen mass-to-charge ratio follows the arc through the slit."#,
    ),
    spot(
        r#"heavy    ╲"#,
        0,
        0,
        r#"Heavier ions have a larger radius and strike the outside."#,
    ),
    spot(
        r#"r = m v / (q B)"#,
        0,
        0,
        r#"The radius depends on mass over charge, so tuning B selects boron, arsenic or phosphorus."#,
    ),
];

const ART_101: &str = r#"# One feed gas, many ions

  BF3 in the source makes
     B+      BF+      BF2+      F+      wall impurities
      │        │        │        │            │
      ▼        ▼        ▼        ▼            ▼
   ═══════════ mass filter slit ═════════════
      only one passes ──▶ BF2+ or B+, as the recipe wants

  neutralised ions can skip the filter and arrive at the
  wrong energy: energy contamination (handled by magnet design)
"#;
const SPOTS_101: &[Spot] = &[
    spot(
        r#"B+      BF+      BF2+"#,
        0,
        0,
        r#"Typical fragments from BF3 include B+ and BF2+. BF2+ is a heavier carrier used for shallow boron implants."#,
    ),
    spot(
        r#"wall impurities"#,
        0,
        0,
        r#"Impurities such as ions from the chamber walls also leave the source."#,
    ),
    spot(
        r#"mass filter slit"#,
        0,
        0,
        r#"Everything except the chosen mass-to-charge ratio is stopped."#,
    ),
    spot(
        r#"only one passes"#,
        0,
        0,
        r#"The recipe chooses which species."#,
    ),
    spot(
        r#"energy contamination"#,
        0,
        0,
        r#"Neutralised ions are not bent by the magnet, so some can slip through at a different energy (textbook)."#,
    ),
];

const ART_102: &str = r#"# Implant versus alternatives

               implant          diffusion / deposition
  any element  yes (magnet)     only some elements
  dose control precise          harder
  film left    none             yes
  depth        set by energy    set by time and heat

  ──▶ no true substitute for many doping steps (textbook)
"#;
const SPOTS_102: &[Spot] = &[
    spot(
        r#"any element  yes (magnet)"#,
        0,
        TO_EOL,
        r#"Mass selection lets implant place essentially any element in silicon."#,
    ),
    spot(
        r#"dose control precise"#,
        0,
        TO_EOL,
        r#"Dose is measured as charge, so it is controlled precisely."#,
    ),
    spot(
        r#"film left    none"#,
        0,
        TO_EOL,
        r#"No film is left on the wafer, as the page notes."#,
    ),
    spot(
        r#"depth        set by energy"#,
        0,
        TO_EOL,
        r#"Implant energy sets the depth of the dopant peak."#,
    ),
    spot(
        r#"no true substitute"#,
        0,
        0,
        r#"For many doping steps, per the textbook claim."#,
    ),
];

const ART_103: &str = r#"# Energy picks the depth

  conc.
   ^  low E      mid E        high E
   | ╱╲         ╱╲           ╱╲
   |╱  ╲       ╱  ╲         ╱  ╲
   └─────────────────────────────▶ depth into silicon
     Rp          Rp           Rp
     shallow    ◀──────────▶  deep

  E = q V    (each unit charge gains q x volts)
  double-charged ions: twice the energy from the same voltage
"#;
const SPOTS_103: &[Spot] = &[
    spot(
        r#"low E"#,
        0,
        0,
        r#"Low energy puts the dopant peak shallow, as needed for source/drain extensions."#,
    ),
    spot(
        r#"high E"#,
        0,
        0,
        r#"High energy puts the peak deep, as needed for retrograde wells, image sensors and power devices."#,
    ),
    spot(
        r#"Rp"#,
        0,
        0,
        r#"Projected range: the depth of the dopant peak."#,
    ),
    spot(
        r#"E = q V"#,
        0,
        0,
        r#"Each unit charge gains q times the accelerating voltage (textbook)."#,
    ),
    spot(
        r#"double-charged ions"#,
        0,
        0,
        r#"Multiply-charged ions reach higher effective energies from the same voltage (textbook)."#,
    ),
];

const ART_104: &str = r#"# Beam energy by class (log scale, approximate)

  keV           0.1    1      10     100    1000
  high current  ██████████████████████              0.1 - 100 keV
  medium current          █████████████████         3 - 500 keV
  high energy                        █████████████  100 keV - 5 MeV

  (patents, Wikipedia, Axcelis; not strict limits)
"#;
const SPOTS_104: &[Spot] = &[
    spot(
        r#"high current "#,
        0,
        TO_EOL,
        r#"About 0.1 - 100 keV: shallow, heavy-dose implants."#,
    ),
    spot(
        r#"medium current"#,
        0,
        TO_EOL,
        r#"Roughly 3 - 500 keV (some to about 600)."#,
    ),
    spot(
        r#"high energy"#,
        0,
        TO_EOL,
        r#"100 keV to 5 MeV, up to 10 MeV in some systems."#,
    ),
    spot(
        r#"(patents, Wikipedia, Axcelis; not strict limits)"#,
        0,
        0,
        r#"The ranges are representative, not hard specs."#,
    ),
];

const ART_105: &str = r#"# Why SiC needs high energy

  silicon      dopant diffuses on anneal  ──▶ shallow implant is fine
  silicon carbide  dopants barely diffuse
                   ──▶ implant must place them deep, hot
                   ──▶ high energy, heavy ions

  2024 unit share (third-party estimate)
    Applied Materials (Varian)  ████████████████████████ 62.65%
    Axcelis                     █████████ 21.19%
"#;
const SPOTS_105: &[Spot] = &[
    spot(
        r#"silicon      dopant diffuses"#,
        0,
        TO_EOL,
        r#"In silicon, anneal moves dopants, so a shallow implant plus heat reaches the target."#,
    ),
    spot(
        r#"silicon carbide  dopants barely diffuse"#,
        0,
        0,
        r#"Dopants barely diffuse in SiC at any temperature (textbook)."#,
    ),
    spot(
        r#"high energy, heavy ions"#,
        0,
        0,
        r#"Which is the niche Axcelis emphasises."#,
    ),
    spot(
        r#"Applied Materials (Varian)"#,
        0,
        TO_EOL,
        r#"62.65% of 2024 implanter unit sales in a third-party estimate, not a filing."#,
    ),
    spot(
        r#"Axcelis                     ████"#,
        0,
        TO_EOL,
        r#"21.19% in the same estimate."#,
    ),
];

const ART_106: &str = r#"# Scan + parallelise

   narrow beam
        │
        ▼
   scan  ◀───────▶  electric or magnetic sweep
     ╱  │  ╲
    ╱   │   ╲       parallelising lens
   ▼    ▼    ▼      all ions arrive at the same angle
  ════════════════ wafer, tilted and spun
  (or: beam fixed, wafer moved mechanically)
"#;
const SPOTS_106: &[Spot] = &[
    spot(
        r#"narrow beam"#,
        0,
        0,
        r#"The beam leaving the analyser is narrow, much smaller than a 300 mm wafer."#,
    ),
    spot(
        r#"scan  ◀───────▶"#,
        0,
        0,
        r#"The beam is scanned electrically or magnetically across the wafer."#,
    ),
    spot(
        r#"parallelising lens"#,
        0,
        0,
        r#"Makes every ion arrive at the same angle, wherever it lands on the wafer."#,
    ),
    spot(
        r#"wafer, tilted and spun"#,
        0,
        0,
        r#"The wafer is tilted and rotated (page figure)."#,
    ),
    spot(
        r#"(or: beam fixed, wafer moved mechanically)"#,
        0,
        0,
        r#"The alternative: move the wafer instead of the beam."#,
    ),
];

const ART_107: &str = r#"# Dose

  Q = (1 / qA) x integral of I(t) dt

  q  charge per ion        A  wafer area
  I  beam current from the Faraday cup

  beam current
   ^      ┌─────────────┐
   |      │ area under  │   integrate until Q = target dose
   |      │ the curve   │
   └──────┴─────────────┴──▶ time

  top dose with economic throughput: ~1e16 /cm2 (Axcelis)
"#;
const SPOTS_107: &[Spot] = &[
    spot(
        r#"Q = (1 / qA) x integral of I(t) dt"#,
        0,
        0,
        r#"Ions per cm2 equals the time integral of beam current over the wafer area, divided by the charge per ion."#,
    ),
    spot(
        r#"I  beam current from the Faraday cup"#,
        0,
        0,
        r#"A Faraday cup measures the current used in the integral."#,
    ),
    spot(
        r#"area under"#,
        0,
        0,
        r#"The accumulated charge. The implant ends when it reaches the target dose."#,
    ),
    spot(
        r#"top dose with economic throughput: ~1e16 /cm2 (Axcelis)"#,
        0,
        0,
        r#"Per Axcelis, the highest dose with economical throughput."#,
    ),
];

const ART_108: &str = r#"# Tilt trades channeling for shadowing

  no tilt: ions line up with crystal planes ──▶ channel deep
  tilt ~7 degrees: ions hit atoms ──▶ normal profile

      ╲ ╲ ╲  ions at ~7 degrees
       ╲ ╲ ╲
   ████ ╲ ╲ ╲      tall fin shadows the base
   ████░░░░░░░░    ░ = shadowed, gets less dose
   ════════════
"#;
const SPOTS_108: &[Spot] = &[
    spot(
        r#"no tilt: ions line up with crystal planes"#,
        0,
        0,
        r#"Ions entering along open crystal corridors travel much deeper than the normal profile predicts."#,
    ),
    spot(
        r#"tilt ~7 degrees"#,
        0,
        0,
        r#"A small tilt, typically around 7 degrees (textbook), avoids channelling."#,
    ),
    spot(
        r#"tall fin shadows the base"#,
        0,
        0,
        r#"On 3D transistors, tilt makes tall features shadow the area next to them."#,
    ),
    spot(
        r#"░ = shadowed, gets less dose"#,
        0,
        0,
        r#"So angle control matters more at FinFET and GAA nodes (textbook)."#,
    ),
];

const ART_109: &str = r#"# Before and after anneal

  after implant               after anneal
  ▒▒▒▒▒▒▒▒▒▒▒▒                ░░░░░░░░░░░░
  ▒▒ B  As ▒▒▒ ◀ random       ░░ B░░As░░░  on lattice sites
  ▒▒▒ P ▒▒▒▒▒▒   inactive     ░░░ P░░░░░░  ACTIVE
  ░░░░░░░░░░░░ crystal below  ░░░░░░░░░░░░
  ▒ amorphous, damaged        ░ crystal regrown

  vacancies and interstitials ──▶ healed
"#;
const SPOTS_109: &[Spot] = &[
    spot(
        r#"after implant"#,
        0,
        0,
        r#"The beam leaves vacancies and interstitials and amorphises the crystal near the surface."#,
    ),
    spot(
        r#"random       "#,
        0,
        0,
        r#"Dopant atoms sit in random places and are electrically inactive."#,
    ),
    spot(r#"after anneal"#, 1, 0, r#"Heating regrows the crystal."#),
    spot(
        r#"on lattice sites"#,
        0,
        0,
        r#"Dopants on lattice sites are electrically active."#,
    ),
    spot(
        r#"vacancies and interstitials ──▶ healed"#,
        0,
        0,
        r#"The point defects from the beam are removed by the anneal."#,
    ),
];

const ART_110: &str = r#"# The trade-off

  slow anneal   ──▶ more diffusion: junction gets deeper
                    (transient enhanced diffusion)
  fast and hot  ──▶ activation, little diffusion

  spike anneal   ramp >= 75 C/s, ~1 s soak
  millisecond    removes implant damage poorly,
                 leakage risk
  microsecond    laser, next card

  anneals keep getting shorter and hotter
"#;
const SPOTS_110: &[Spot] = &[
    spot(
        r#"slow anneal"#,
        0,
        0,
        r#"Dopants have time to diffuse, which deepens the junction."#,
    ),
    spot(
        r#"fast and hot"#,
        0,
        0,
        r#"The aim: high activation with little diffusion."#,
    ),
    spot(
        r#"spike anneal   ramp >= 75 C/s, ~1 s soak"#,
        0,
        0,
        r#"From the anneal patent: a fast ramp and short soak gives high activation and little diffusion."#,
    ),
    spot(
        r#"millisecond    removes implant damage poorly,"#,
        0,
        0,
        r#"From the page's sources: damage is removed poorly, with a leakage risk."#,
    ),
    spot(
        r#"anneals keep getting shorter and hotter"#,
        0,
        0,
        r#"The trend that ends in microsecond laser anneal."#,
    ),
];

const ART_111: &str = r#"# Anneal time versus node

  planar     ████████████████████ long, cooler
  FinFET     ██████████ shorter
  GAA        ████ spike / ms / laser

  (schematic of the trend; shorter and hotter at each step)

  each node: less allowed heat ──▶ new anneal tools
  anneal suppliers differ from implant suppliers (textbook)
"#;
const SPOTS_111: &[Spot] = &[
    spot(
        r#"planar     ███"#,
        0,
        TO_EOL,
        r#"Older nodes tolerate longer thermal cycles."#,
    ),
    spot(
        r#"FinFET     ███"#,
        0,
        TO_EOL,
        r#"Shrinking junctions leave less thermal budget."#,
    ),
    spot(
        r#"GAA        ███"#,
        0,
        TO_EOL,
        r#"Very little thermal budget, so spike, millisecond and laser anneals."#,
    ),
    spot(
        r#"(schematic of the trend; shorter and hotter at each step)"#,
        0,
        0,
        r#"This is an illustration of direction, not measured durations."#,
    ),
    spot(
        r#"anneal suppliers differ from implant suppliers (textbook)"#,
        0,
        0,
        r#"So anneal is a separate investment angle."#,
    ),
];

const ART_112: &str = r#"# Tune B to pick the element

  B low      ─ heavy ions pass:  As+  (75)
  B medium   ─ mid ions pass:    P+   (31)
  B high     ─ light ions pass:  B+   (11)
  (illustrative: field tuned per species)

  beam in ══▶ ┌ magnet ┐ ══▶ slit ══▶ single species
              └────────┘
  everything else hits the slit and stops
"#;
const SPOTS_112: &[Spot] = &[
    spot(
        r#"B low      ─ heavy ions pass:  As+  (75)"#,
        0,
        0,
        r#"Arsenic is heavy (mass number 75), so it needs a different field than lighter dopants."#,
    ),
    spot(
        r#"B medium   ─ mid ions pass:    P+   (31)"#,
        0,
        0,
        r#"Phosphorus, mass number 31."#,
    ),
    spot(
        r#"B high     ─ light ions pass:  B+   (11)"#,
        0,
        0,
        r#"Boron, mass number 11."#,
    ),
    spot(
        r#"(illustrative: field tuned per species)"#,
        0,
        0,
        r#"The labels show the idea; real settings depend on beam energy and charge state."#,
    ),
    spot(
        r#"everything else hits the slit and stops"#,
        0,
        0,
        r#"Only one mass-to-charge ratio is selected (page figure)."#,
    ),
];

const ART_113: &str = r#"# Vacuum all the way

  source ══ analyser ══ accel ══ scan ══ wafer
  ───────────── vacuum throughout ─────────────

  gas molecule in the path
     ion ──▶ ● collision ──▶ charge state or energy changes
                          ──▶ wrong dose, wrong depth

  mass resolution: set by magnet and slit width
"#;
const SPOTS_113: &[Spot] = &[
    spot(
        r#"source ══ analyser"#,
        0,
        0,
        r#"The whole beam line is under vacuum."#,
    ),
    spot(
        r#"vacuum throughout"#,
        0,
        0,
        r#"So the beam hits nothing but the wafer."#,
    ),
    spot(
        r#"● collision"#,
        0,
        0,
        r#"A collision with a gas molecule can change an ion's charge state or energy (textbook)."#,
    ),
    spot(
        r#"mass resolution: set by magnet and slit width"#,
        0,
        0,
        r#"Resolving power depends on the magnet radius and slit width; the beam must be clean enough to pick one species (textbook)."#,
    ),
];

const ART_114: &str = r#"# Transmission

  extracted current   ████████████████████ 100%
  reaches the wafer   ██████████████ transmission (depends on design)
  lost in analyser, column, scan lens

  higher transmission ──▶ shorter implant per wafer

  Axcelis Purion: three tools    Applied: one offering (as described)
    high current                   analysts argue Axcelis gives
    medium current                 more process flexibility
    high energy
"#;
const SPOTS_114: &[Spot] = &[
    spot(
        r#"extracted current   ████"#,
        0,
        TO_EOL,
        r#"All the current pulled out of the source."#,
    ),
    spot(
        r#"reaches the wafer   ████"#,
        0,
        TO_EOL,
        r#"Only a fraction arrives. The exact figure depends on tool and recipe, so none is given here."#,
    ),
    spot(
        r#"higher transmission"#,
        0,
        0,
        r#"The main throughput lever: shorter implant time per wafer."#,
    ),
    spot(
        r#"Axcelis Purion: three tools"#,
        0,
        0,
        r#"Separate high-current, medium-current and high-energy tools, per analysts' descriptions."#,
    ),
    spot(
        r#"Applied: one offering (as described)"#,
        0,
        0,
        r#"Described in secondary sources as a single tool against Axcelis's three."#,
    ),
];

const ART_115: &str = r#"# Faraday cup loop

   beam ══▶ ┌────────────┐
            │ metal cup  │──▶ ammeter ──▶ current I
            └────────────┘
                              │
                              ▼
            integrate I over time
            Q = total charge / (q x wafer area)
                              │
              Q reaches target? ──▶ stop the implant
"#;
const SPOTS_115: &[Spot] = &[
    spot(
        r#"metal cup"#,
        0,
        0,
        r#"Catches the beam. Each ion carries known charge, so current measures ion flow."#,
    ),
    spot(r#"ammeter"#, 0, 0, r#"Reads the beam current directly."#),
    spot(
        r#"integrate I over time"#,
        0,
        0,
        r#"Charge accumulates as the integral of current."#,
    ),
    spot(
        r#"Q = total charge / (q x wafer area)"#,
        0,
        0,
        r#"Ions per cm2: the dose in the page equation."#,
    ),
    spot(
        r#"Q reaches target? ──▶ stop the implant"#,
        0,
        0,
        r#"This feedback ends the implant at the target dose."#,
    ),
];

const ART_116: &str = r#"# Dose range by class (ions/cm2, exponent of 10)

                10  11  12  13  14  15  16  17
  high energy   █████████████
  medium current    █████████████
  high current                  █████████████

  error of a few percent shifts sheet resistance and
  threshold voltage (textbook)
"#;
const SPOTS_116: &[Spot] = &[
    spot(
        r#"high energy"#,
        0,
        TO_EOL,
        r#"1e10 to 1e13 ions per cm2 (approximate, from patents and Wikipedia)."#,
    ),
    spot(
        r#"medium current"#,
        0,
        TO_EOL,
        r#"1e11 to 1e14 ions per cm2."#,
    ),
    spot(
        r#"high current"#,
        0,
        TO_EOL,
        r#"1e14 to 1e17 ions per cm2."#,
    ),
    spot(
        r#"error of a few percent shifts sheet resistance and"#,
        0,
        0,
        r#"So dose accuracy is a core specification (textbook)."#,
    ),
];

const ART_117: &str = r#"# What corrupts the reading

  secondary electrons leave the cup ──▶ reads too high
     fix: suppression (magnetic or electric)
  beam glitch ──▶ current drops ──▶ dose error
  cup contamination ──▶ drifts the reading

  charge builds up on the wafer
     ions + ──▶ + + + + ──▶ gate oxide breakdown
     electron flood gun supplies electrons to neutralise
  (textbook)
"#;
const SPOTS_117: &[Spot] = &[
    spot(
        r#"secondary electrons leave the cup"#,
        0,
        0,
        r#"Electrons knocked out of the cup add apparent current, so the reading is wrong without suppression (textbook)."#,
    ),
    spot(
        r#"beam glitch"#,
        0,
        0,
        r#"A dropout reduces delivered dose."#,
    ),
    spot(
        r#"cup contamination"#,
        0,
        0,
        r#"A dirty cup changes the measurement."#,
    ),
    spot(
        r#"electron flood gun supplies electrons to neutralise"#,
        0,
        0,
        r#"Electron flood systems neutralise charge build-up on the wafer (textbook)."#,
    ),
    spot(
        r#"gate oxide breakdown"#,
        0,
        0,
        r#"Charge build-up can damage thin gate oxides (textbook)."#,
    ),
];

const ART_118: &str = r#"# Looking down a crystal axis

   ion ↓  ↓       ↓
   ●  ●  ●  ●  ●  ●     atoms in rows
   ●  ●  ●  ●  ●  ●
   ●  ●  ●  ●  ●  ●
   ●  ●  ●  ●  ●  ●
        ↓                ion slides down the corridor
        ·                scatters little, goes deep

  concentration
   ^ ╲╲
   |   ╲╲___________  channeling tail
   └──────────────────▶ depth
"#;
const SPOTS_118: &[Spot] = &[
    spot(
        r#"atoms in rows"#,
        0,
        0,
        r#"Looking along a crystal axis, atoms line up and leave open corridors between rows."#,
    ),
    spot(
        r#"ion slides down the corridor"#,
        0,
        0,
        r#"Ions in a corridor scatter little and slow down slowly."#,
    ),
    spot(
        r#"scatters little, goes deep"#,
        0,
        0,
        r#"They travel much deeper than the normal profile predicts."#,
    ),
    spot(
        r#"channeling tail"#,
        0,
        0,
        r#"A long tail of dopant beyond the intended depth ruins shallow junctions."#,
    ),
];

const ART_119: &str = r#"# Tilt, or destroy the crystal first

  tilt + rotate               pre-amorphise
   ╲ ╲ ╲                      heavy ion beam first
    ● ● ● ●  beam hits        ▒▒▒▒▒▒▒▒▒▒ no crystal near surface
    ● ● ● ●  atoms, no        ▒▒▒▒▒▒▒▒▒▒ ──▶ nothing to channel
    ● ● ● ●  corridor         ● ● ● ● ●
  cost: shadowing at 3D       cost: damage to repair at anneal;
        features                    end-of-range defects can leak
"#;
const SPOTS_119: &[Spot] = &[
    spot(
        r#"tilt + rotate"#,
        0,
        0,
        r#"Tilt and rotate the wafer so the beam does not align with a crystal axis."#,
    ),
    spot(
        r#"pre-amorphise"#,
        0,
        0,
        r#"Damage the surface first, for example with a heavy ion beam, so there is no crystal to channel along."#,
    ),
    spot(
        r#"cost: shadowing at 3D"#,
        0,
        0,
        r#"Tilt makes tall 3D features shadow neighbours, which complicates GAA and FinFET structures (textbook)."#,
    ),
    spot(
        r#"cost: damage to repair at anneal;"#,
        0,
        0,
        r#"Pre-amorphisation adds damage that must be repaired at anneal, and leftover end-of-range defects can cause leakage."#,
    ),
];

const ART_120: &str = r#"# Profile without channeling

  conc.
   ^            higher dose: taller
   |         ╱╲
   |        ╱  ╲  ◀ peak at Rp
   |      ╱      ╲
   └─────────────────▶ depth
        more energy: Rp moves deeper

  stopping: nuclear + electronic slow the ions
  tail beyond the junction ──▶ leakage, short-channel effects
"#;
const SPOTS_120: &[Spot] = &[
    spot(
        r#"higher dose: taller"#,
        0,
        0,
        r#"More ions make a taller peak."#,
    ),
    spot(
        r#"peak at Rp"#,
        0,
        0,
        r#"The peak sits at the projected range."#,
    ),
    spot(
        r#"more energy: Rp moves deeper"#,
        0,
        0,
        r#"Higher beam energy pushes the peak deeper."#,
    ),
    spot(
        r#"stopping: nuclear + electronic slow the ions"#,
        0,
        0,
        r#"The two ways ions lose energy in the crystal."#,
    ),
    spot(
        r#"tail beyond the junction ──▶ leakage, short-channel effects"#,
        0,
        0,
        r#"Dopant beyond the intended junction hurts tiny transistors."#,
    ),
];

const ART_121: &str = r#"# High-current class

  energy     0.1 - 100 keV           shallow
  dose       1e14 - 1e17 /cm2        heavy
  current    up to ~25-30 mA

  used for  source/drain and extensions   (B, As, P)
            shallow, heavily doped regions

  top dose with economical throughput: ~1e16 /cm2 (Axcelis)
"#;
const SPOTS_121: &[Spot] = &[
    spot(
        r#"energy     0.1 - 100 keV"#,
        0,
        TO_EOL,
        r#"Low energy keeps the dopant near the surface."#,
    ),
    spot(
        r#"dose       1e14 - 1e17 /cm2"#,
        0,
        TO_EOL,
        r#"The heaviest doses of the three classes."#,
    ),
    spot(
        r#"current    up to ~25-30 mA"#,
        0,
        TO_EOL,
        r#"Large beam currents are needed to deliver that dose in reasonable time."#,
    ),
    spot(
        r#"used for  source/drain and extensions"#,
        0,
        0,
        r#"Per the page's usage table (textbook)."#,
    ),
    spot(
        r#"top dose with economical throughput: ~1e16 /cm2 (Axcelis)"#,
        0,
        0,
        r#"Per Axcelis, doses above this cost too much beam time to be economical."#,
    ),
];

const ART_122: &str = r#"# Shrink the junction, lose throughput

  junction depth      ██████████ ──▶ ████ ──▶ ██
                      older          newer     leading edge

  needs: low energy + high dose + tight anneal
  low energy ──▶ space charge ──▶ less beam current
                              ──▶ longer implant time per wafer

  design answer: extract fast, decelerate late
"#;
const SPOTS_122: &[Spot] = &[
    spot(
        r#"junction depth"#,
        0,
        0,
        r#"Illustrative of the trend: junctions get shallower at each node."#,
    ),
    spot(
        r#"needs: low energy + high dose + tight anneal"#,
        0,
        0,
        r#"The conflict that drives high-current design."#,
    ),
    spot(
        r#"low energy ──▶ space charge"#,
        0,
        0,
        r#"Space charge limits low-energy beam current (textbook)."#,
    ),
    spot(
        r#"design answer: extract fast, decelerate late"#,
        0,
        0,
        r#"Deceleration after extraction keeps the beam tight in transit."#,
    ),
];

const ART_123: &str = r#"# Which class does what (textbook usage)

  class      energy         dose        makes
  high cur.  0.1-100 keV    1e14-1e17   source/drain, extensions
  medium     3-500 keV      1e11-1e14   wells, channel, Vt, halos
  high en.   100 keV-5 MeV  1e10-1e13   deep wells: sensors, power

  (approximate; patents, Wikipedia and Axcelis say not strict)
"#;
const SPOTS_123: &[Spot] = &[
    spot(
        r#"high cur.  0.1-100 keV"#,
        0,
        TO_EOL,
        r#"Source/drain and extension doping."#,
    ),
    spot(
        r#"medium     3-500 keV"#,
        0,
        TO_EOL,
        r#"Wells, channels, threshold adjust and halos."#,
    ),
    spot(
        r#"high en.   100 keV-5 MeV"#,
        0,
        TO_EOL,
        r#"Deep wells for image sensors and power devices."#,
    ),
    spot(
        r#"(approximate; patents, Wikipedia and Axcelis say not strict)"#,
        0,
        0,
        r#"Representative ranges, not hard limits."#,
    ),
];

const ART_124: &str = r#"# Implanter unit sales 2024 (third-party estimate)

  Applied Mat.  ████████████████████████████████████ 62.65%
  Axcelis       ████████████████ 21.19%
  Others (calc) ████████████ 16.16%

  Applied: about 686 units (same estimate; not a filing)
  'Others' is arithmetic: 100 - 62.65 - 21.19
"#;
const SPOTS_124: &[Spot] = &[
    spot(
        r#"Applied Mat.  ████"#,
        0,
        TO_EOL,
        r#"About 62.65% of 2024 unit sales in a third-party estimate."#,
    ),
    spot(
        r#"Axcelis       ████"#,
        0,
        TO_EOL,
        r#"21.19% in the same estimate."#,
    ),
    spot(
        r#"Others (calc)"#,
        0,
        TO_EOL,
        r#"Derived: 100 minus the two named shares."#,
    ),
    spot(
        r#"Applied: about 686 units"#,
        0,
        0,
        r#"Per the same third-party estimate; not a filing."#,
    ),
];

const ART_125: &str = r#"# Applied's share

  2011  ██████████████████████████████████████████████ ~75%
        (Varian's share when Applied bought it)
  2022  ██████████████████████████████████████ ~62%
        (one analyst piece)
  2024  ███████████████████████████████████████ 62.65%
        (third-party estimate)

  roughly stable recently, down from the peak
"#;
const SPOTS_125: &[Spot] = &[
    spot(
        r#"2011  ███"#,
        0,
        TO_EOL,
        r#"Varian held about 75% when Applied bought it in 2011."#,
    ),
    spot(
        r#"2022  ███"#,
        0,
        TO_EOL,
        r#"One analyst piece had Applied at 62%."#,
    ),
    spot(
        r#"2024  ███"#,
        0,
        TO_EOL,
        r#"62.65% in a third-party estimate."#,
    ),
    spot(
        r#"roughly stable recently, down from the peak"#,
        0,
        0,
        r#"Treat the figures as estimates."#,
    ),
];

const ART_126: &str = r#"# Where implant sits at Applied

  deposition          ████████████████████ bigger
  selective removal   ████████████ bigger
  implant             ██ small slice

  incumbent: fabs qualify tools layer by layer
             ──▶ hard to dislodge (textbook)

  vs Axcelis Purion: three tools   Applied: one offering
  Applied SiC-specific model: not found in search
"#;
const SPOTS_126: &[Spot] = &[
    spot(
        r#"deposition          ███"#,
        0,
        TO_EOL,
        r#"Applied is much bigger in deposition (schematic, not to scale)."#,
    ),
    spot(
        r#"selective removal   ███"#,
        0,
        TO_EOL,
        r#"Also much bigger than implant (schematic)."#,
    ),
    spot(
        r#"implant             ██"#,
        0,
        TO_EOL,
        r#"A small slice of Applied's business, so not the stock driver."#,
    ),
    spot(
        r#"incumbent: fabs qualify tools layer by layer"#,
        0,
        0,
        r#"Which makes the position hard to dislodge (textbook)."#,
    ),
    spot(
        r#"Applied SiC-specific model: not found in search"#,
        0,
        0,
        r#"The search did not return a current Applied SiC implanter model."#,
    ),
];

const ART_127: &str = r#"# Axcelis Purion suite

  Purion H    high current      source/drain, extensions
  Purion M    medium current    wells, channel, halos
  Purion XE   high energy       deep wells, SiC

  FY2025 revenue
    implant   ██████████████████████████████████████ 98.2%
    other     ▏ 1.8% (arithmetic)
  (aggregator figure)
"#;
const SPOTS_127: &[Spot] = &[
    spot(
        r#"Purion H    high current"#,
        0,
        TO_EOL,
        r#"Covers the high-current class."#,
    ),
    spot(
        r#"Purion M    medium current"#,
        0,
        TO_EOL,
        r#"Covers the medium-current class."#,
    ),
    spot(
        r#"Purion XE   high energy"#,
        0,
        TO_EOL,
        r#"The Purion XE and EXE handle the high-energy needs of 150 and 200 mm SiC wafers (analyst commentary)."#,
    ),
    spot(
        r#"implant   ████"#,
        0,
        TO_EOL,
        r#"98.2% of FY2025 revenue (aggregator figure)."#,
    ),
    spot(
        r#"other     ▏"#,
        0,
        TO_EOL,
        r#"1.8% is arithmetic: 100 minus 98.2."#,
    ),
];

const ART_128: &str = r#"# Merger timeline

  Oct 2025       agreed to merge with Veeco (VECO)
  6 Feb 2026     Axcelis stockholders approve
  UK review      ended with a no-action letter
  Sweden         condition waived
  30 Jun 2026    10-Q: still needs China SAMR approval
  2H 2026        completion expected

  status: pending unless a later filing says closed
"#;
const SPOTS_128: &[Spot] = &[
    spot(
        r#"Oct 2025       agreed to merge"#,
        0,
        TO_EOL,
        r#"Axcelis agreed to merge with Veeco in October 2025."#,
    ),
    spot(
        r#"6 Feb 2026     Axcelis stockholders approve"#,
        0,
        TO_EOL,
        r#"Stockholders approved on February 6, 2026."#,
    ),
    spot(
        r#"UK review      ended with a no-action letter"#,
        0,
        TO_EOL,
        r#"From the latest 10-Q."#,
    ),
    spot(
        r#"30 Jun 2026    10-Q: still needs China SAMR approval"#,
        0,
        TO_EOL,
        r#"The 10-Q for the quarter ended June 30, 2026 says final approval from China's SAMR was still needed."#,
    ),
    spot(
        r#"2H 2026        completion expected"#,
        0,
        TO_EOL,
        r#"Completion expected in the second half of 2026."#,
    ),
    spot(
        r#"status: pending unless a later filing says closed"#,
        0,
        0,
        r#"Check for a later filing."#,
    ),
];

const ART_129: &str = r#"# SiC implant (analyst view, not verified)

  Axcelis   ████████████████████████████████████ ~70-80%
  others    ██████████ ~20-30%

  why SiC needs high-energy, hot implant
    dopants barely diffuse in SiC (textbook)
  tools: Purion XE and EXE for 150 and 200 mm SiC wafers
"#;
const SPOTS_129: &[Spot] = &[
    spot(
        r#"Axcelis   ████"#,
        0,
        TO_EOL,
        r#"One analyst view puts Axcelis at roughly 70-80% of SiC implant. Not verified."#,
    ),
    spot(
        r#"others    ███"#,
        0,
        TO_EOL,
        r#"What is left, by subtraction."#,
    ),
    spot(
        r#"dopants barely diffuse in SiC (textbook)"#,
        0,
        0,
        r#"So implant has to place them deep and hot."#,
    ),
    spot(
        r#"tools: Purion XE and EXE for 150 and 200 mm SiC wafers"#,
        0,
        0,
        r#"From analyst commentary and secondary sites."#,
    ),
];

const ART_130: &str = r#"# SEN structure

  Axcelis (ACLS)  ──── 50% ────┐
                               ├──▶ SEN
  Sumitomo Heavy (6302.T) 50% ─┘
                                    │
                                    ▼
                    implanters sold and serviced in Japan
                    (leader in Japan per the 2004 10-K)
"#;
const SPOTS_130: &[Spot] = &[
    spot(
        r#"Axcelis (ACLS)"#,
        0,
        0,
        r#"One half of the joint venture."#,
    ),
    spot(
        r#"Sumitomo Heavy (6302.T)"#,
        0,
        0,
        r#"Sumitomo Heavy Industries owns the other half of the joint venture."#,
    ),
    spot(r#"──▶ SEN"#, 0, 0, r#"The joint venture entity."#),
    spot(
        r#"implanters sold and serviced in Japan"#,
        0,
        0,
        r#"A local partner lets Axcelis serve the Japanese market (textbook interpretation of the JV structure)."#,
    ),
    spot(
        r#"(leader in Japan per the 2004 10-K)"#,
        0,
        0,
        r#"From a 2004 filing, so the current position is not confirmed."#,
    ),
];

const ART_131: &str = r#"# Confidence

  2004 10-K     50/50 JV, leader in Japan     found
  current stake                               not confirmed
  current scope                               not confirmed
  current share                               not confirmed
  newer sources                               none returned

  next step: the most recent Axcelis 10-K
"#;
const SPOTS_131: &[Spot] = &[
    spot(
        r#"2004 10-K     50/50 JV, leader in Japan     found"#,
        0,
        TO_EOL,
        r#"The only filing found, from 2004."#,
    ),
    spot(
        r#"current stake"#,
        0,
        TO_EOL,
        r#"The current ownership split is not confirmed by any source found."#,
    ),
    spot(
        r#"current scope"#,
        0,
        TO_EOL,
        r#"What SEN does today is not confirmed by any source found."#,
    ),
    spot(
        r#"current share"#,
        0,
        TO_EOL,
        r#"SEN's present Japan market share is not confirmed by any source found."#,
    ),
    spot(
        r#"next step: the most recent Axcelis 10-K"#,
        0,
        0,
        r#"It will state the current status of the SEN relationship."#,
    ),
];

const ART_132: &str = r#"# Why a local partner helps (textbook)

  core markets for implanters
    Japan   Korea   Taiwan

  local partner
    ──▶ qualification at Japanese fabs
    ──▶ export-control compliance

  Veeco merger effect on the JV: no source found
"#;
const SPOTS_132: &[Spot] = &[
    spot(
        r#"Japan   Korea   Taiwan"#,
        0,
        0,
        r#"Core markets for chipmakers who buy implanters."#,
    ),
    spot(
        r#"qualification at Japanese fabs"#,
        0,
        0,
        r#"A local partner can matter for qualification (textbook)."#,
    ),
    spot(
        r#"export-control compliance"#,
        0,
        0,
        r#"Also relevant to compliance (textbook)."#,
    ),
    spot(
        r#"Veeco merger effect on the JV: no source found"#,
        0,
        0,
        r#"Whether the merger changes how the JV is presented is unknown."#,
    ),
];

const ART_133: &str = r#"# Laser anneal

  laser pulse  ≈≈≈≈≈≈≈≈≈≈≈≈  10-200 us
  ▓▓▓▓▓▓▓▓▓▓▓▓  top layer hot, up to ~1350 C (vendor claim)
  ░░░░░░░░░░░░  below: stays cool
  ░░░░░░░░░░░░
  ═════════════ wafer

  high activation, almost no diffusion
  + laser after spike anneal raised activation (page source)
"#;
const SPOTS_133: &[Spot] = &[
    spot(
        r#"laser pulse  ≈≈≈≈"#,
        0,
        0,
        r#"Pulses of 10-200 microseconds, per the page's source."#,
    ),
    spot(
        r#"top layer hot, up to ~1350 C (vendor claim)"#,
        0,
        0,
        r#"A vendor claim for the peak temperature at the surface, not an independent measurement."#,
    ),
    spot(
        r#"below: stays cool"#,
        0,
        0,
        r#"Only the thin top layer heats, so metal gates and contacts already built are spared (textbook)."#,
    ),
    spot(
        r#"+ laser after spike anneal raised activation (page source)"#,
        0,
        0,
        r#"Reported in the anneal source."#,
    ),
];

const ART_134: &str = r#"# The ladder of anneals

  furnace     ░░░░░░░░░░░░░░░░░░░░░░ minutes (older)
  spike       ████ ~1 s soak, ramp >= 75 C/s
  millisecond ██ poor damage removal, leakage risk
  laser       ▏ 10-200 us, up to ~1350 C (vendor claim)

  shorter ──▶ less diffusion, junctions stay shallow
  hotter  ──▶ more activation
"#;
const SPOTS_134: &[Spot] = &[
    spot(
        r#"furnace     ░░░"#,
        0,
        TO_EOL,
        r#"The older approach, long and cooler (schematic)."#,
    ),
    spot(
        r#"spike       ████"#,
        0,
        TO_EOL,
        r#"Ramp of at least 75 C/s with about a 1 s soak, for high activation and little diffusion."#,
    ),
    spot(
        r#"millisecond ██"#,
        0,
        TO_EOL,
        r#"Millisecond anneals remove implant damage poorly and risk leakage."#,
    ),
    spot(
        r#"laser       ▏"#,
        0,
        TO_EOL,
        r#"10-200 microseconds, up to about 1350 C (vendor claim)."#,
    ),
    spot(
        r#"shorter ──▶ less diffusion"#,
        0,
        0,
        r#"Keeps junctions shallow."#,
    ),
];

const ART_135: &str = r#"# What can go wrong

  pattern-dependent heating
     film A  absorbs ▓▓▓▓  hot
     film B  absorbs ▒▒    cooler   ──▶ uneven activation
  melt-related defects
  leakage if damage is not fully healed

  suppliers of anneal tools differ from implanter suppliers
  (textbook)
"#;
const SPOTS_135: &[Spot] = &[
    spot(
        r#"film A  absorbs"#,
        0,
        0,
        r#"Different films absorb the laser light differently (textbook)."#,
    ),
    spot(
        r#"film B  absorbs"#,
        0,
        0,
        r#"So heating depends on the pattern beneath."#,
    ),
    spot(
        r#"melt-related defects"#,
        0,
        0,
        r#"Melting can leave defects."#,
    ),
    spot(
        r#"leakage if damage is not fully healed"#,
        0,
        0,
        r#"Incomplete repair of implant damage causes leakage."#,
    ),
    spot(
        r#"suppliers of anneal tools differ from implanter suppliers"#,
        0,
        0,
        r#"So it is a separate investment angle (textbook)."#,
    ),
];

const ART_136: &str = r#"# SPM burns organics off

  resist (carbon, hydrogen)  +  H2SO4 / H2O2
        ──▶  CO2  +  H2O

  patent example
    99% H2SO4 : 1% H2O2     140 C     10 min
    then SC1                 55 C     10 min

  peroxide is used up fast at 140 C
    ──▶ dose it inline just before the wafer
    ──▶ or recirculate and replenish a bath (textbook)
"#;
const SPOTS_136: &[Spot] = &[
    spot(
        r#"resist (carbon, hydrogen)"#,
        0,
        0,
        r#"Photoresist and other carbon residue are the target."#,
    ),
    spot(
        r#"──▶  CO2  +  H2O"#,
        0,
        0,
        r#"Oxidation turns the organics into gas and water."#,
    ),
    spot(
        r#"99% H2SO4 : 1% H2O2     140 C     10 min"#,
        0,
        0,
        r#"The patent example on this page."#,
    ),
    spot(
        r#"then SC1                 55 C     10 min"#,
        0,
        0,
        r#"The patent follows SPM with an SC1 step at 55 C."#,
    ),
    spot(
        r#"peroxide is used up fast at 140 C"#,
        0,
        0,
        r#"So tools dose fresh peroxide inline or replenish a recirculating bath (textbook)."#,
    ),
];

const ART_137: &str = r#"# What SPM leaves behind

  after SPM
    wafer  ═══════════════
    thin chemical oxide   ▒▒▒▒▒▒
    sulfur residue        · · ·
         │
         ▼
  rinse ──▶ DHF dip removes the oxide ──▶ rinse

  waste: hot concentrated acid ──▶ own drain line
  trend: ozone or plasma ash to use less sulfuric acid (textbook)
"#;
const SPOTS_137: &[Spot] = &[
    spot(
        r#"thin chemical oxide"#,
        0,
        0,
        r#"SPM leaves a thin chemical oxide on silicon."#,
    ),
    spot(
        r#"sulfur residue"#,
        0,
        0,
        r#"Sulfur residue must be rinsed away."#,
    ),
    spot(
        r#"DHF dip removes the oxide"#,
        0,
        0,
        r#"This is why a DHF step follows the rinse."#,
    ),
    spot(
        r#"waste: hot concentrated acid"#,
        0,
        0,
        r#"Needs its own drain line."#,
    ),
    spot(
        r#"trend: ozone or plasma ash to use less sulfuric acid (textbook)"#,
        0,
        0,
        r#"Fabs increasingly look at these to cut sulfuric acid use."#,
    ),
];

const ART_138: &str = r#"# Clean follows every strip

  implant ──▶ strip resist ──▶ SPM clean
  etch    ──▶ strip resist ──▶ SPM clean
  CMP     ──▶ clean

  more layers per chip ──▶ more strips ──▶ more cleans
  (wet-clean step count rises with layer count: textbook)
"#;
const SPOTS_138: &[Spot] = &[
    spot(
        r#"implant ──▶ strip resist"#,
        0,
        TO_EOL,
        r#"Implant leaves hardened resist that must be stripped and cleaned."#,
    ),
    spot(
        r#"etch    ──▶ strip resist"#,
        0,
        TO_EOL,
        r#"Etch is followed by strip and clean."#,
    ),
    spot(
        r#"CMP     ──▶ clean"#,
        0,
        TO_EOL,
        r#"Polishing leaves slurry residue that needs cleaning."#,
    ),
    spot(
        r#"more layers per chip"#,
        0,
        0,
        r#"So wet-clean step counts rise with layer count (textbook)."#,
    ),
];

const ART_139: &str = r#"# Flush before the next chemistry

  SC1 (base) ──▶ DI rinse ──▶ SC2 (acid)
  without the rinse:
     base + acid on the wafer ──▶ salts and particles

  recipe source: DI rinse between each of
  HF, SC1 and SC2
"#;
const SPOTS_139: &[Spot] = &[
    spot(
        r#"SC1 (base)"#,
        0,
        0,
        r#"A basic mixture of ammonium hydroxide, peroxide and water."#,
    ),
    spot(
        r#"DI rinse"#,
        0,
        0,
        r#"Flushes the first chemistry off before the next arrives."#,
    ),
    spot(
        r#"SC2 (acid)"#,
        0,
        0,
        r#"An acidic mixture of hydrochloric acid, peroxide and water."#,
    ),
    spot(
        r#"base + acid on the wafer"#,
        0,
        0,
        r#"They would meet on the surface and form salts and particles."#,
    ),
    spot(
        r#"recipe source: DI rinse between each of"#,
        0,
        0,
        r#"The page's recipe source says to rinse between each of the HF, SC1 and SC2 steps."#,
    ),
];

const ART_140: &str = r#"# The rinse must be cleaner than the wafer

  18.2 megohm-cm   textbook spec (no source found)

  impurities in the water re-contaminate the wafer
    ions       silica       bacteria       particles

  after DHF the bare silicon is reactive:
    dissolved O2 ──▶ native oxide regrows
    fix: degas the water, or N2-blanketed rinse (textbook)
"#;
const SPOTS_140: &[Spot] = &[
    spot(
        r#"18.2 megohm-cm"#,
        0,
        0,
        r#"The resistivity of ultra-pure water; a textbook spec with no source found for this card."#,
    ),
    spot(
        r#"ions       silica"#,
        0,
        0,
        r#"Dissolved ions and silica can deposit on the wafer."#,
    ),
    spot(
        r#"bacteria       particles"#,
        0,
        0,
        r#"Biological and particle contamination also re-contaminate the wafer."#,
    ),
    spot(
        r#"dissolved O2 ──▶ native oxide regrows"#,
        0,
        0,
        r#"Dissolved oxygen can regrow native oxide on bare silicon after DHF (textbook)."#,
    ),
    spot(
        r#"fix: degas the water, or N2-blanketed rinse (textbook)"#,
        0,
        0,
        r#"Some fabs degas or use N2-blanketed rinse."#,
    ),
];

const ART_141: &str = r#"# Two ways to rinse

  single-wafer                    batch bench
  nozzle ──▶ DI stream            ┌──────────────┐
      │                           │ overflow tank│
  ═══ wafer spins ═══             │ ▮▮▮▮▮▮▮▮▮▮▮▮ │ cassette sits in
      │ off the edge              └──────────────┘ flowing water
  rinse time = lost wafers/hour   many wafers share the tank
"#;
const SPOTS_141: &[Spot] = &[
    spot(
        r#"single-wafer"#,
        0,
        0,
        r#"A nozzle delivers DI water while the wafer spins, so rinse time reduces wafers per hour."#,
    ),
    spot(
        r#"batch bench"#,
        0,
        0,
        r#"Wafers sit in an overflow rinse tank, many at a time (textbook)."#,
    ),
    spot(
        r#"overflow tank"#,
        0,
        0,
        r#"Fresh water flows in and overflows out so contaminants leave."#,
    ),
    spot(
        r#"rinse time = lost wafers/hour"#,
        0,
        0,
        r#"In single-wafer tools rinse time directly costs throughput."#,
    ),
];

const ART_142: &str = r#"# DHF removes the oxide

  before                          after DHF
  contaminants  · ·  ·            ····· gone with the oxide
  native oxide  ▒▒▒▒▒▒▒▒▒▒▒       (stripped)
  silicon       ░░░░░░░░░░░       silicon  ░░░░░░░░░░░

  SiO2 + 6HF ──▶ H2SiF6 + 2H2O    (textbook)
  HF : water  usually 1000:1 or 200:1
"#;
const SPOTS_142: &[Spot] = &[
    spot(
        r#"native oxide  ▒▒▒"#,
        0,
        0,
        r#"A thin oxide that grows on silicon in air."#,
    ),
    spot(
        r#"contaminants  · ·  ·"#,
        0,
        0,
        r#"Contaminants trapped in the oxide are lifted off when it dissolves."#,
    ),
    spot(
        r#"(stripped)"#,
        0,
        0,
        r#"HF etches silicon dioxide, so the oxide and what it traps are removed."#,
    ),
    spot(
        r#"SiO2 + 6HF ──▶ H2SiF6 + 2H2O"#,
        0,
        0,
        r#"The overall chemistry (textbook)."#,
    ),
    spot(
        r#"HF : water  usually 1000:1 or 200:1"#,
        0,
        0,
        r#"From the patent text on this page."#,
    ),
];

const ART_143: &str = r#"# Hydrogen-terminated silicon

   H   H   H   H   H   H     hydrogen caps every surface bond
   │   │   │   │   │   │
  Si──Si──Si──Si──Si──Si     hydrophobic: water beads up
  Si──Si──Si──Si──Si──Si

  very clean, but reactive
  ──▶ move to the next step or a controlled ambient quickly
"#;
const SPOTS_143: &[Spot] = &[
    spot(
        r#"hydrogen caps every surface bond"#,
        0,
        0,
        r#"After DHF the silicon surface is terminated with hydrogen (textbook)."#,
    ),
    spot(
        r#"hydrophobic: water beads up"#,
        0,
        0,
        r#"The surface repels water (textbook)."#,
    ),
    spot(
        r#"very clean, but reactive"#,
        0,
        0,
        r#"The bare surface will oxidise again if left in air."#,
    ),
    spot(
        r#"move to the next step or a controlled ambient quickly"#,
        0,
        0,
        r#"Textbook handling advice."#,
    ),
];

const ART_144: &str = r#"# Where DHF sits

  page's source    HF ──▶ SC1 ──▶ SC2          DI rinse between each
  SPM first        SPM ──▶ rinse ──▶ DHF ──▶ ...

  HF attacks many films at advanced nodes
    thin gate oxide     over-etch changes the device
    low-k, oxide spacer dimensions drift
  ──▶ hold concentration, time and temperature tight
  HF is toxic: its own waste treatment
"#;
const SPOTS_144: &[Spot] = &[
    spot(
        r#"page's source    HF"#,
        0,
        0,
        r#"The classic RCA order on this page."#,
    ),
    spot(
        r#"SPM first        SPM"#,
        0,
        0,
        r#"A recipe that starts with SPM needs a rinse and DHF to remove the chemical oxide it leaves."#,
    ),
    spot(
        r#"thin gate oxide"#,
        0,
        0,
        r#"Over-etching changes device dimensions (textbook)."#,
    ),
    spot(
        r#"low-k, oxide spacer"#,
        0,
        0,
        r#"HF attacks many films used at advanced nodes."#,
    ),
    spot(
        r#"HF is toxic: its own waste treatment"#,
        0,
        0,
        r#"The waste stream needs its own treatment."#,
    ),
];

const ART_145: &str = r#"# One SC1 cycle

  1  H2O2 grows a thin oxide      ▒▒▒▒▒▒▒▒▒▒▒
        o  particle sits on it    o
  2  NH4OH dissolves a little     ░▒▒▒▒░░▒▒▒▒   undercut
        of the oxide              ───┴─────
  3  particle is lifted off       o ──▶ away in the liquid
  repeat: each cycle goes a little further
"#;
const SPOTS_145: &[Spot] = &[
    spot(
        r#"1  H2O2 grows a thin oxide"#,
        0,
        0,
        r#"Peroxide oxidises the silicon surface (textbook)."#,
    ),
    spot(
        r#"2  NH4OH dissolves a little"#,
        0,
        0,
        r#"The base etches some of that oxide, freeing the underside of the particle."#,
    ),
    spot(
        r#"undercut"#,
        0,
        0,
        r#"The particle loses its grip as the surface beneath it dissolves."#,
    ),
    spot(
        r#"3  particle is lifted off"#,
        0,
        0,
        r#"The particle floats away in the liquid."#,
    ),
    spot(
        r#"repeat: each cycle goes a little further"#,
        0,
        0,
        r#"The cycle is mild, so SC1 removes silicon only slowly."#,
    ),
];

const ART_146: &str = r#"# Same charge, so they push apart

       −  −  −
      −  o  −     particle, negative at pH ~10
       −  −  −
         ▲ ▼      repulsion
  ═══ − − − − − ═══   wafer surface, negative

  pH about 10 (textbook): particle stays in solution
  does not settle back onto the wafer
"#;
const SPOTS_146: &[Spot] = &[
    spot(
        r#"particle, negative at pH ~10"#,
        0,
        0,
        r#"At a pH near 10 the particle carries a negative charge (textbook)."#,
    ),
    spot(
        r#"repulsion"#,
        0,
        0,
        r#"Like charges push apart, keeping the particle off the surface."#,
    ),
    spot(
        r#"wafer surface, negative"#,
        0,
        0,
        r#"The wafer surface is also negatively charged at this pH (textbook)."#,
    ),
    spot(
        r#"pH about 10 (textbook): particle stays in solution"#,
        0,
        0,
        r#"This is why removed particles do not redeposit."#,
    ),
];

const ART_147: &str = r#"# Harder cleaning, rougher wafer

  stronger recipe ◀──────────────────▶ gentler recipe
  hotter, longer                       cooler, shorter
  more particles removed               fewer removed
  rougher, pitted silicon              smoother silicon

  patent range     30-80 C, 5-30 min
  advanced nodes   dilute SC1 + megasonic energy
  ACM SAPS (vendor claim)  up to 99.2% particle removal
"#;
const SPOTS_147: &[Spot] = &[
    spot(
        r#"stronger recipe"#,
        0,
        0,
        r#"Hotter and longer removes more particles but costs silicon and smoothness."#,
    ),
    spot(
        r#"gentler recipe"#,
        0,
        0,
        r#"Protects the surface but may leave particles."#,
    ),
    spot(
        r#"patent range     30-80 C, 5-30 min"#,
        0,
        0,
        r#"The SC1 range in the patent on this page."#,
    ),
    spot(
        r#"advanced nodes   dilute SC1 + megasonic energy"#,
        0,
        0,
        r#"At advanced nodes SC1 is combined with megasonic energy rather than made stronger."#,
    ),
    spot(
        r#"ACM SAPS (vendor claim)  up to 99.2% particle removal"#,
        0,
        0,
        r#"A vendor claim from an ACM Research article."#,
    ),
];

const ART_148: &str = r#"# SC2: metal in, chloride out

  metal on the wafer  +  HCl / H2O2
        ──▶  soluble metal chloride  ──▶ rinses away

  vendor bench   H2O : H2O2 : HCl = 160:4:1
                 about 50 C, 20 min

  why after SC1: SC1 can leave behind or deposit
  iron and aluminium hydroxides (textbook)
"#;
const SPOTS_148: &[Spot] = &[
    spot(
        r#"metal on the wafer"#,
        0,
        0,
        r#"Iron, aluminium and other metals left from earlier steps."#,
    ),
    spot(
        r#"soluble metal chloride"#,
        0,
        0,
        r#"Chlorides dissolve in water, so a rinse removes them."#,
    ),
    spot(
        r#"vendor bench   H2O : H2O2 : HCl = 160:4:1"#,
        0,
        0,
        r#"Vendor bench recipe on the page."#,
    ),
    spot(
        r#"about 50 C, 20 min"#,
        0,
        0,
        r#"Temperature and time for the vendor SC2 bench recipe, per the page."#,
    ),
    spot(
        r#"why after SC1:"#,
        0,
        0,
        r#"SC1 can leave behind or deposit iron and aluminium hydroxides, so SC2 follows (textbook)."#,
    ),
];

const ART_149: &str = r#"# Invisible contamination

  metal atoms on the surface
       ● ●  ●
  ═══ gate oxide ═══        ──▶ degraded integrity
  silicon  ● diffuses in    ──▶ shorter carrier lifetime
                            ──▶ leakage, failing devices
  no visible defect to see

  so: purity grades, DI water metals, tank materials
      are specified tightly
"#;
const SPOTS_149: &[Spot] = &[
    spot(
        r#"metal atoms on the surface"#,
        0,
        0,
        r#"Transition metals and mobile ions are the concern (textbook)."#,
    ),
    spot(
        r#"degraded integrity"#,
        0,
        0,
        r#"Gate oxide integrity suffers (textbook)."#,
    ),
    spot(
        r#"shorter carrier lifetime"#,
        0,
        0,
        r#"Minority-carrier lifetime falls (textbook)."#,
    ),
    spot(
        r#"leakage, failing devices"#,
        0,
        0,
        r#"Devices can fail without any visible defect."#,
    ),
    spot(
        r#"purity grades, DI water metals, tank materials"#,
        0,
        0,
        r#"Metal control is a yield matter, so these are specified tightly."#,
    ),
];

const ART_150: &str = r#"# Variants in the field (textbook)

  classic       SC2: HCl / H2O2 / water
  modern        dilute acid steps
                chelating additives bind the metal
  hardware      quartz or PFA tanks, must not leach metal

  real fabs run many variants after almost every
  etch, strip and CMP step
"#;
const SPOTS_150: &[Spot] = &[
    spot(
        r#"classic       SC2"#,
        0,
        0,
        r#"The original RCA second step."#,
    ),
    spot(
        r#"modern        dilute acid steps"#,
        0,
        0,
        r#"Often replace the full SC2 (textbook)."#,
    ),
    spot(
        r#"chelating additives bind the metal"#,
        0,
        0,
        r#"Chelators hold metal ions in solution so they rinse away."#,
    ),
    spot(
        r#"quartz or PFA tanks, must not leach metal"#,
        0,
        0,
        r#"Batch benches must avoid being their own metal source (textbook)."#,
    ),
    spot(
        r#"real fabs run many variants"#,
        0,
        0,
        r#"The page notes variants after almost every etch, strip and CMP step."#,
    ),
];

const ART_151: &str = r#"# Spin / IPA dry

   N2 + IPA vapour ──▶ nozzle
          │
  ═══════ wafer spins ═══════   water thrown off the edge
          │
   IPA lowers surface tension

  watermark = droplet evaporates, leaves silica or residue
  goal: no marks, and no lines pulled together
"#;
const SPOTS_151: &[Spot] = &[
    spot(
        r#"N2 + IPA vapour"#,
        0,
        0,
        r#"Nitrogen carries isopropanol vapour onto the wafer."#,
    ),
    spot(
        r#"wafer spins"#,
        0,
        0,
        r#"Spinning throws most of the water off the edge."#,
    ),
    spot(
        r#"IPA lowers surface tension"#,
        0,
        0,
        r#"Lower surface tension means less force on fine features."#,
    ),
    spot(
        r#"watermark = droplet evaporates"#,
        0,
        0,
        r#"Dissolved silica or residue is left where a droplet dries."#,
    ),
];

const ART_152: &str = r#"# No interface, no surface tension

  liquid ──▶ gas   a meniscus sweeps through the pattern
  scCO2            no liquid-gas boundary at all

  drawbacks (patent text)
    slow supply and discharge of the fluid
    IPA can redeposit on depressurisation
      ──▶ drying marks
"#;
const SPOTS_152: &[Spot] = &[
    spot(
        r#"liquid ──▶ gas"#,
        0,
        0,
        r#"Normal drying drags a meniscus through the pattern."#,
    ),
    spot(
        r#"scCO2            no liquid-gas boundary at all"#,
        0,
        0,
        r#"Supercritical CO2 removes the interface, so surface tension is effectively zero."#,
    ),
    spot(
        r#"slow supply and discharge of the fluid"#,
        0,
        0,
        r#"A drawback named in patent text."#,
    ),
    spot(
        r#"IPA can redeposit on depressurisation"#,
        0,
        0,
        r#"Leaving drying marks, per patent text."#,
    ),
];

const ART_153: &str = r#"# Where drying happens

  batch bench          cassette ──▶ lifts out of the final tank
                                    through IPA vapour

  single-wafer         same chamber: rinse, spin, N2 sweep
                       one wafer at a time

  tall thin patterns   see the Marangoni card
"#;
const SPOTS_153: &[Spot] = &[
    spot(
        r#"batch bench"#,
        0,
        0,
        r#"Wafers lift out of the final tank through an IPA vapour zone (textbook)."#,
    ),
    spot(
        r#"single-wafer"#,
        0,
        0,
        r#"Spin and N2 sweep happen in the same chamber (textbook)."#,
    ),
    spot(
        r#"tall thin patterns"#,
        0,
        0,
        r#"The Marangoni card covers the drying choice that matters most for these."#,
    ),
];

const ART_154: &str = r#"# Swing arm over a spinning wafer

  arm ──╮
        ▼ nozzle sweeps centre ──▶ edge
  ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈   liquid film
  ═════════ wafer ═══════════════
       │ spindle spins
  centrifugal force: fresh chemistry out,
  spent liquid + particles off the edge into the bowl
"#;
const SPOTS_154: &[Spot] = &[
    spot(
        r#"arm ──╮"#,
        0,
        0,
        r#"A swing arm carries the chemical nozzle across the wafer."#,
    ),
    spot(
        r#"nozzle sweeps centre ──▶ edge"#,
        0,
        0,
        r#"The sweep gives every part of the wafer the same dwell time."#,
    ),
    spot(
        r#"liquid film"#,
        0,
        0,
        r#"Spin speed creates the film (textbook)."#,
    ),
    spot(
        r#"spindle spins"#,
        0,
        0,
        r#"The wafer sits face up on a spinning chuck or edge pins."#,
    ),
    spot(
        r#"spent liquid + particles off the edge into the bowl"#,
        0,
        0,
        r#"Centrifugal force carries the spent chemistry, with the particles it lifted, to the bowl."#,
    ),
];

const ART_155: &str = r#"# Single-wafer versus batch

                 single-wafer          batch bench
  chemistry      fresh each wafer      bath shared by many
  contamination  low cross-talk        wafer to wafer risk
  throughput     fewer wafers/hour     high
  fix            many chambers/tool    one big tank set

  point-of-use heating keeps SPM and SC1 fresh (textbook)
"#;
const SPOTS_155: &[Spot] = &[
    spot(
        r#"chemistry      fresh each wafer"#,
        0,
        0,
        r#"The main advantage of single-wafer tools."#,
    ),
    spot(
        r#"contamination  low cross-talk"#,
        0,
        0,
        r#"Batch baths can cross-contaminate wafers."#,
    ),
    spot(
        r#"throughput     fewer wafers/hour"#,
        0,
        0,
        r#"The tradeoff, as the comparison box on the page says."#,
    ),
    spot(
        r#"fix            many chambers/tool"#,
        0,
        0,
        r#"A fab buys many chambers per tool to make up the throughput."#,
    ),
    spot(
        r#"point-of-use heating keeps SPM and SC1 fresh (textbook)"#,
        0,
        0,
        r#"Short-lived mixtures are heated just before they land."#,
    ),
];

const ART_156: &str = r#"# Leading single-wafer clean vendors (per aggregators)

  SCREEN (7735.T)
  Tokyo Electron (8035.T)
  Lam Research (LRCX)
  SEMES   (Samsung affiliate, textbook)

  no reliable share split found
  (SCREEN claimed share figures are low quality: see BATCH)
"#;
const SPOTS_156: &[Spot] = &[
    spot(
        r#"SCREEN (7735.T)"#,
        0,
        0,
        r#"Named first by the page's aggregators."#,
    ),
    spot(
        r#"Tokyo Electron (8035.T)"#,
        0,
        0,
        r#"Also a leading single-wafer clean vendor."#,
    ),
    spot(
        r#"Lam Research (LRCX)"#,
        0,
        0,
        r#"Sells clean beside etch and deposition."#,
    ),
    spot(
        r#"SEMES   (Samsung affiliate, textbook)"#,
        0,
        0,
        r#"A Samsung affiliate (textbook)."#,
    ),
    spot(
        r#"no reliable share split found"#,
        0,
        0,
        r#"The aggregator share figures are low quality."#,
    ),
];

const ART_157: &str = r#"# Megasonic cleaning

    transducer ~1 MHz
        ║ ║ ║ acoustic waves
        ▼ ▼ ▼
  ≈≈ ○ ≈≈ ○ ≈≈ ○ ≈≈   liquid film with micro-bubbles
  ═════ o ══════════ o ═══ wafer, particles o
  bubbles thin the boundary layer, push particles loose
  cavitation (bubble collapse) cleans, and can also damage
"#;
const SPOTS_157: &[Spot] = &[
    spot(
        r#"transducer ~1 MHz"#,
        0,
        0,
        r#"Sends acoustic waves at about a megahertz through the liquid."#,
    ),
    spot(
        r#"liquid film with micro-bubbles"#,
        0,
        0,
        r#"The oscillating pressure creates microscopic bubbles."#,
    ),
    spot(
        r#"o ══════════ o"#,
        0,
        0,
        r#"Particles that chemistry alone has undercut."#,
    ),
    spot(
        r#"bubbles thin the boundary layer, push particles loose"#,
        0,
        0,
        r#"The mechanism described on this page."#,
    ),
    spot(
        r#"cavitation (bubble collapse) cleans, and can also damage"#,
        0,
        0,
        r#"Cavitation is the double-edged part."#,
    ),
];

const ART_158: &str = r#"# Patent test on 55 nm features

  pulse cycle 0.1 ms   ▏ 0 damage sites
  pulse cycle 2 ms     ████████████████████████████████ 1,216 sites

  predicted damage-free at 1 MHz or below

  removal  ◀── usable window ──▶  damage
  window shrinks as features shrink
"#;
const SPOTS_158: &[Spot] = &[
    spot(
        r#"pulse cycle 0.1 ms"#,
        0,
        TO_EOL,
        r#"No damage in the patent test."#,
    ),
    spot(
        r#"pulse cycle 2 ms"#,
        0,
        TO_EOL,
        r#"1,216 damage sites on 55 nm features in the same test."#,
    ),
    spot(
        r#"predicted damage-free at 1 MHz or below"#,
        0,
        0,
        r#"The patent's prediction."#,
    ),
    spot(
        r#"window shrinks as features shrink"#,
        0,
        0,
        r#"Smaller features tolerate less energy."#,
    ),
];

const ART_159: &str = r#"# Where the energy limit bites

  GAA nanosheets   fragile, suspended ──▶ little energy allowed
  3D NAND holes    deep, narrow       ──▶ cavitation in the hole

  frequency
    80 kHz, 120 kHz   ultrasonic bath (one university RCA tank)
    ~1 MHz            megasonic, single wafer

  vendor article: megasonic is reaching its limit
  for the smallest killer defects
"#;
const SPOTS_159: &[Spot] = &[
    spot(
        r#"GAA nanosheets   fragile, suspended"#,
        0,
        0,
        r#"Fragile nanosheets limit how much energy can be used (textbook)."#,
    ),
    spot(
        r#"3D NAND holes    deep, narrow"#,
        0,
        0,
        r#"Deep holes limit usable energy too (textbook)."#,
    ),
    spot(
        r#"80 kHz, 120 kHz   ultrasonic bath"#,
        0,
        0,
        r#"Lower frequencies, used for bulk bath cleaning."#,
    ),
    spot(
        r#"~1 MHz            megasonic, single wafer"#,
        0,
        0,
        r#"Higher frequency, gentler on small features."#,
    ),
    spot(
        r#"vendor article: megasonic is reaching its limit"#,
        0,
        0,
        r#"A vendor article says conventional megasonic cleaning is reaching its limit for the smallest killer defects."#,
    ),
];

const ART_160: &str = r#"# Ring stack

       ═══ wafer spins ═══
   ┌──── ring 1 ────┐  ──▶ drain: acid
   ├──── ring 2 ────┤  ──▶ drain: base
   ├──── ring 3 ────┤  ──▶ drain: solvent
   └────────────────┘
  rings rise and fall: each chemistry exits its own channel

  mixing is dangerous (acid + base, solvent + oxidiser)
  and ruins recycling (textbook)
"#;
const SPOTS_160: &[Spot] = &[
    spot(
        r#"ring 1"#,
        0,
        0,
        r#"The ring height is chosen so the liquid flung off hits the right ring."#,
    ),
    spot(
        r#"drain: acid"#,
        0,
        0,
        r#"Acid waste stays on its own line."#,
    ),
    spot(r#"drain: base"#, 0, 0, r#"Base waste on a separate line."#),
    spot(r#"drain: solvent"#, 0, 0, r#"Solvent waste likewise."#),
    spot(
        r#"mixing is dangerous (acid + base, solvent + oxidiser)"#,
        0,
        0,
        r#"And would ruin recycling (textbook)."#,
    ),
];

const ART_161: &str = r#"# What the drains carry

  hot H2SO4 / H2O2      SPM
  HF                    DHF       toxic
  NH4OH / H2O2          SC1
  HCl / H2O2            SC2

  chokepoint: HF and H2SO4 waste handling
  ──▶ part of the tool's cost and permitting
"#;
const SPOTS_161: &[Spot] = &[
    spot(
        r#"hot H2SO4 / H2O2"#,
        0,
        TO_EOL,
        r#"Hot sulfuric/peroxide mixture."#,
    ),
    spot(
        r#"HF                    DHF"#,
        0,
        TO_EOL,
        r#"Hydrofluoric acid is toxic and needs its own waste treatment."#,
    ),
    spot(r#"NH4OH / H2O2"#, 0, TO_EOL, r#"Ammonia and peroxide."#),
    spot(
        r#"HCl / H2O2"#,
        0,
        TO_EOL,
        r#"Hydrochloric acid and peroxide."#,
    ),
    spot(
        r#"chokepoint: HF and H2SO4 waste handling"#,
        0,
        0,
        r#"The page lists this as a chokepoint for the process."#,
    ),
];

const ART_162: &str = r#"# Mist from one chemistry meets the next

  wafer 1  SC1 mist ──▶ lingers in the chamber
  wafer 2  acid arrives ──▶ reacts with the mist
         ──▶ watermarks, haze, particle adders

  vendors differ in chamber design (textbook)
    airflow     back-rinse of the bowl     N2 curtains
"#;
const SPOTS_162: &[Spot] = &[
    spot(
        r#"wafer 1  SC1 mist"#,
        0,
        0,
        r#"Mist from one chemistry can linger in the chamber."#,
    ),
    spot(
        r#"wafer 2  acid arrives"#,
        0,
        0,
        r#"A different chemistry can react with the leftover mist."#,
    ),
    spot(
        r#"watermarks, haze, particle adders"#,
        0,
        0,
        r#"How cross-contamination shows up on the next wafer."#,
    ),
    spot(
        r#"airflow     back-rinse of the bowl     N2 curtains"#,
        0,
        0,
        r#"Chamber design features that separate tool vendors (textbook)."#,
    ),
];

const ART_163: &str = r#"# Marangoni drying

  plain water               IPA introduced at the edge
   |▒|  ≈≈≈  |▒|             |▒|        |▒|
   |▒|  ≈≈≈  |▒|             |▒|  ──▶    |▒|   water pulled away
   |▒|__≈≈≈__|▒|             |▒|_________|▒|
  meniscus pulls the lines   IPA lowers surface tension,
  together: stiction         flow drains the water (textbook)
"#;
const SPOTS_163: &[Spot] = &[
    spot(
        r#"plain water"#,
        0,
        0,
        r#"Water between tall thin lines forms a curved meniscus."#,
    ),
    spot(
        r#"meniscus pulls the lines"#,
        0,
        0,
        r#"As the meniscus recedes it pulls neighbours together. Stiff lines spring back; weak ones stick (stiction)."#,
    ),
    spot(
        r#"IPA introduced at the edge"#,
        0,
        0,
        r#"Isopropanol lowers the surface tension at the receding edge."#,
    ),
    spot(
        r#"water pulled away"#,
        0,
        0,
        r#"A surface-tension gradient drives flow that pulls water off the surface (textbook)."#,
    ),
];

const ART_164: &str = r#"# Stiction rate by drying method (Applied abstract)

  Marangoni (solvent-assisted)  ██████████████ ~40%
  sublimation drying            ████████████████████████████████ ~90%
  supercritical CO2             ▏ none

  patent source: even a lower-surface-tension fluid
  such as HFE has not made IPA drying fully safe
"#;
const SPOTS_164: &[Spot] = &[
    spot(
        r#"Marangoni (solvent-assisted)"#,
        0,
        TO_EOL,
        r#"About 40% stiction in the Applied Materials abstract."#,
    ),
    spot(
        r#"sublimation drying"#,
        0,
        TO_EOL,
        r#"About 90% stiction in the same Applied Materials abstract, the worst of the three methods."#,
    ),
    spot(
        r#"supercritical CO2"#,
        0,
        TO_EOL,
        r#"No stiction reported."#,
    ),
    spot(
        r#"patent source: even a lower-surface-tension fluid"#,
        0,
        0,
        r#"Another patent source says HFE has not made IPA drying fully safe from collapse."#,
    ),
];

const ART_165: &str = r#"# Cost of zero surface tension

  benefit  no liquid-gas interface
  cost     slow fluid supply and discharge
           IPA can redeposit on depressurisation
             ──▶ drying marks
           metal electrodes may be etched at some
           chamber temperatures

  risk structures (textbook)
    high-aspect-ratio fins    GAA stacks    DRAM capacitors
"#;
const SPOTS_165: &[Spot] = &[
    spot(
        r#"benefit  no liquid-gas interface"#,
        0,
        0,
        r#"Surface tension is effectively zero."#,
    ),
    spot(
        r#"slow fluid supply and discharge"#,
        0,
        0,
        r#"Hurts throughput, a drawback named in patent text."#,
    ),
    spot(
        r#"IPA can redeposit on depressurisation"#,
        0,
        0,
        r#"Leaves drying marks."#,
    ),
    spot(
        r#"metal electrodes may be etched at some"#,
        0,
        0,
        r#"A reported drawback at some chamber temperatures."#,
    ),
    spot(
        r#"high-aspect-ratio fins    GAA stacks    DRAM capacitors"#,
        0,
        0,
        r#"The typical risk structures for pattern collapse (textbook)."#,
    ),
];

const ART_166: &str = r#"# Batch wet bench: one cassette through the tanks

  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
  │ SPM  │─▶│  DI  │─▶│ SC1  │─▶│ SC2  │─▶│ IPA  │
  │ tank │  │rinse │  │ tank │  │ tank │  │ dry  │
  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘
  25-50 wafers per cassette, shared heated tanks

  + high throughput per square metre
  - big chemical volumes
  - wafers share the bath: cross-contamination risk
"#;
const SPOTS_166: &[Spot] = &[
    spot(r#"SPM  │"#, 0, 0, r#"The first tank, for organics."#),
    spot(r#"SC1 "#, 0, 0, r#"Particle removal tank."#),
    spot(
        r#"SC2 "#,
        0,
        0,
        r#"The metal-removal tank, SC2, follows SC1 in the sequence."#,
    ),
    spot(
        r#"25-50 wafers per cassette, shared heated tanks"#,
        0,
        0,
        r#"The page's figure for a cassette in a batch bench."#,
    ),
    spot(
        r#"- wafers share the bath: cross-contamination risk"#,
        0,
        0,
        r#"Wafer-to-wafer or backside cross-contamination is a risk because all wafers share the bath."#,
    ),
];

const ART_167: &str = r#"# SCREEN SPE

  FY to Mar 2026
    segment sales   485,982 million yen (-6.5%)
    operating profit 122,707 million yen

  claimed single-wafer share (low-quality aggregators)
    2024 est.       █████████████████████████ 45%
    end-2025 est.   ███████████████████ 38%

  company says only: top global share, no number
"#;
const SPOTS_167: &[Spot] = &[
    spot(
        r#"segment sales   485,982 million yen (-6.5%)"#,
        0,
        0,
        r#"Semiconductor equipment segment sales for the fiscal year to March 2026."#,
    ),
    spot(
        r#"operating profit 122,707 million yen"#,
        0,
        0,
        r#"Segment operating profit for the same year."#,
    ),
    spot(
        r#"2024 est.       ████"#,
        0,
        TO_EOL,
        r#"45% in one low-quality aggregator."#,
    ),
    spot(
        r#"end-2025 est.   ████"#,
        0,
        TO_EOL,
        r#"38% in another. Treat both as low quality."#,
    ),
    spot(
        r#"company says only: top global share, no number"#,
        0,
        0,
        r#"SCREEN SPE itself gives no number."#,
    ),
];

const ART_168: &str = r#"# Who uses which (textbook)

  critical steps at advanced nodes   ──▶ single-wafer
    fragile patterns, tight control, lower damage

  throughput- and cost-driven steps  ──▶ batch
    tolerant layers, big volumes

  SCREEN claims leadership in both styles
"#;
const SPOTS_168: &[Spot] = &[
    spot(
        r#"critical steps at advanced nodes"#,
        0,
        0,
        r#"Single-wafer gives fresh chemistry and tight control for fragile patterns."#,
    ),
    spot(
        r#"throughput- and cost-driven steps"#,
        0,
        0,
        r#"Batch stays where throughput and cost dominate."#,
    ),
    spot(
        r#"SCREEN claims leadership in both styles"#,
        0,
        0,
        r#"SCREEN SPE claims top global share in single-wafer, batch and spin scrubbers."#,
    ),
];

const ART_169: &str = r#"# Etch + clean share of WFE (Yole; dry and wet combined)

  early 2022  ███████████████████████████ ~27%
  H1 2024     ███████████████████ ~19%

  mix effect: 2024 WFE stable, then a 2025 surge
  other segments grew faster
  ──▶ not proof that cleaning is shrinking in absolute terms
"#;
const SPOTS_169: &[Spot] = &[
    spot(
        r#"early 2022  ███"#,
        0,
        TO_EOL,
        r#"About 27% of wafer fab equipment spending, per Yole."#,
    ),
    spot(r#"H1 2024     ███"#, 0, TO_EOL, r#"About 19% in H1 2024."#),
    spot(
        r#"mix effect: 2024 WFE stable, then a 2025 surge"#,
        0,
        0,
        r#"The denominator changed as other segments grew."#,
    ),
    spot(
        r#"not proof that cleaning is shrinking in absolute terms"#,
        0,
        0,
        r#"The share fell because the pie changed, not necessarily the clean business."#,
    ),
];

const ART_170: &str = r#"# Names to know

  SCREEN Holdings (7735.T)   wet clean specialist
  Tokyo Electron (8035.T)    also big
  Lam Research (LRCX)        clean beside etch, deposition
  SEMES                      Samsung affiliate (textbook)

  wet ETCH shares (not cleaning), one 2025 page
    Applied        ████████████████ 15.7%
    TEL            ██████████████ 13.8%
    Lam            ████████████▌ 12.7%
    Hitachi H-T    ███████ 7.2%
"#;
const SPOTS_170: &[Spot] = &[
    spot(
        r#"SCREEN Holdings (7735.T)"#,
        0,
        0,
        r#"Claims #1 in single-wafer, batch and scrubbers."#,
    ),
    spot(
        r#"Tokyo Electron (8035.T)"#,
        0,
        0,
        r#"Also a big clean supplier."#,
    ),
    spot(
        r#"Lam Research (LRCX)"#,
        0,
        0,
        r#"Sells clean beside etch and deposition."#,
    ),
    spot(r#"SEMES"#, 0, 0, r#"A Samsung affiliate (textbook)."#),
    spot(
        r#"Applied        ████"#,
        0,
        TO_EOL,
        r#"15.7% of wet etch (not cleaning) on one 2025 page."#,
    ),
    spot(
        r#"Hitachi H-T    ███"#,
        0,
        TO_EOL,
        r#"7.2% in the same listing."#,
    ),
];

const ART_171: &str = r#"# Demand drivers (textbook)

  more layers        ──▶ more strips and cleans per wafer
  smaller features   ──▶ gentler clean needed
  GAA, 3D NAND       ──▶ fragile structures, deep holes

  but clean is a smaller, slower-moving corner of WFE
  than lithography, etch or deposition
  ──▶ rarely drives a stock on its own
"#;
const SPOTS_171: &[Spot] = &[
    spot(
        r#"more layers"#,
        0,
        0,
        r#"More wet steps per wafer (textbook)."#,
    ),
    spot(r#"smaller features"#, 0, 0, r#"Need gentler cleaning."#),
    spot(
        r#"GAA, 3D NAND"#,
        0,
        0,
        r#"Fragile structures and deep holes constrain the clean design."#,
    ),
    spot(
        r#"rarely drives a stock on its own"#,
        0,
        0,
        r#"Clean is smaller and slower-moving than litho, etch or deposition."#,
    ),
];

const ART_172: &str = r#"# SC1 recipes: H2O : H2O2 : NH4OH

  patent range      1000:1:1 to 1:1:1
  patent preferred  100:1:1 to 5:1:1
  patent temp/time  30-80 C, 5-30 min
  vendor bench      40:1:1, about 50 C, 20 min

  no single standard: fabs tune ratio, temperature and
  time per layer (particles vs silicon loss vs roughness)
"#;
const SPOTS_172: &[Spot] = &[
    spot(
        r#"patent range      1000:1:1 to 1:1:1"#,
        0,
        TO_EOL,
        r#"The full range in the patent on this page."#,
    ),
    spot(
        r#"patent preferred  100:1:1 to 5:1:1"#,
        0,
        TO_EOL,
        r#"The preferred sub-range."#,
    ),
    spot(
        r#"patent temp/time  30-80 C, 5-30 min"#,
        0,
        TO_EOL,
        r#"Temperature and time range."#,
    ),
    spot(
        r#"vendor bench      40:1:1, about 50 C, 20 min"#,
        0,
        TO_EOL,
        r#"A vendor bench recipe from the page."#,
    ),
    spot(r#"no single standard"#, 0, 0, r#"Fabs tune per layer."#),
];

const ART_173: &str = r#"# Two steps, repeated

  Si + 2 H2O2  ──▶  SiO2 + 2 H2O      peroxide grows oxide
  SiO2 + NH4OH ──▶  dissolves         base removes it

  oxide caps how fast the silicon is consumed
  ──▶ self-limiting (textbook, unsourced)
"#;
const SPOTS_173: &[Spot] = &[
    spot(
        r#"Si + 2 H2O2  ──▶  SiO2 + 2 H2O"#,
        0,
        TO_EOL,
        r#"Peroxide oxidises the silicon surface (textbook, unsourced)."#,
    ),
    spot(
        r#"SiO2 + NH4OH ──▶  dissolves"#,
        0,
        TO_EOL,
        r#"The base dissolves the oxide (textbook)."#,
    ),
    spot(
        r#"oxide caps how fast the silicon is consumed"#,
        0,
        0,
        r#"So the process is self-limiting in how far it eats into the silicon."#,
    ),
];

const ART_174: &str = r#"# Bath problems

  too hot or too long   ──▶ roughness, thickness loss
  ammonia + peroxide decay with temperature
                        ──▶ bath drifts over time
  incomplete rinse      ──▶ ammonium salts left behind

  leading edge: dilute SC1 + megasonic,
  not a stronger SC1
"#;
const SPOTS_174: &[Spot] = &[
    spot(
        r#"too hot or too long"#,
        0,
        TO_EOL,
        r#"Roughness and thickness loss (textbook)."#,
    ),
    spot(
        r#"ammonia + peroxide decay with temperature"#,
        0,
        0,
        r#"Both species decay, so the bath changes with time."#,
    ),
    spot(
        r#"incomplete rinse"#,
        0,
        TO_EOL,
        r#"Leaves ammonium salts (textbook)."#,
    ),
    spot(
        r#"leading edge: dilute SC1 + megasonic,"#,
        0,
        0,
        r#"Leading-edge nodes pair diluted SC1 with megasonic energy rather than strengthening it."#,
    ),
];

const ART_175: &str = r#"# Wafer cleaning equipment market, USD billion

  Report A 2024   ████████████████████████████ 7.39
  Report B 2024   ███████████████████████████████████ 9.28
  Report C 2023   ██████████████████████████████████████████ 10.92

  largest AND oldest year ──▶ definitions differ
  what is counted varies (textbook inference)
  nothing here links to company filings
"#;
const SPOTS_175: &[Spot] = &[
    spot(
        r#"Report A 2024"#,
        0,
        TO_EOL,
        r#"7.39 billion USD for 2024 in the first aggregator report."#,
    ),
    spot(
        r#"Report B 2024"#,
        0,
        TO_EOL,
        r#"9.28 billion USD for 2024 in the second aggregator report."#,
    ),
    spot(
        r#"Report C 2023"#,
        0,
        TO_EOL,
        r#"10.92 billion USD: the largest figure for the oldest year."#,
    ),
    spot(
        r#"largest AND oldest year"#,
        0,
        0,
        r#"Which already tells you the definitions differ."#,
    ),
    spot(
        r#"what is counted varies (textbook inference)"#,
        0,
        0,
        r#"Wet benches, single-wafer, scrubbers, dry clean, ash and strip, consumables or service may or may not be included."#,
    ),
];

const ART_176: &str = r#"# Two anchors, neither converts cleanly

  SCREEN SPE segment, FY to Mar 2026
    485,982 million yen
    (one company, in yen, more than clean)

  Yole etch + clean share of WFE
    about 19% in H1 2024
    (dry and wet together)

  ──▶ no clean-only market size falls out of either
"#;
const SPOTS_176: &[Spot] = &[
    spot(
        r#"485,982 million yen"#,
        0,
        0,
        r#"SCREEN's semiconductor equipment segment sales for the fiscal year to March 2026."#,
    ),
    spot(
        r#"(one company, in yen, more than clean)"#,
        0,
        0,
        r#"The segment includes more than cleaning."#,
    ),
    spot(
        r#"about 19% in H1 2024"#,
        0,
        0,
        r#"Yole's combined etch-and-clean share of WFE."#,
    ),
    spot(
        r#"(dry and wet together)"#,
        0,
        0,
        r#"So it cannot be split into a clean-only figure."#,
    ),
];

const ART_177: &str = r#"# Which numbers to trust

  weaker    aggregator headline market sizes
  better    company segment results
              SCREEN, Tokyo Electron, Lam
            SEMI equipment data

  the spread between reports is itself the warning
"#;
const SPOTS_177: &[Spot] = &[
    spot(
        r#"weaker    aggregator headline market sizes"#,
        0,
        0,
        r#"Definitions vary and sources are not linked to filings."#,
    ),
    spot(
        r#"better    company segment results"#,
        0,
        0,
        r#"SCREEN, Tokyo Electron and Lam report segment results."#,
    ),
    spot(
        r#"SEMI equipment data"#,
        0,
        0,
        r#"Industry equipment statistics are a better anchor than aggregator headlines."#,
    ),
    spot(
        r#"the spread between reports is itself the warning"#,
        0,
        0,
        r#"Use it as a warning, not a data point."#,
    ),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::screens::diagrams_vis::check;

    #[test]
    fn every_group_c_visual_resolves() {
        let all: &[(&str, &str, &str)] = &[
            ("DEVELOP", r#"PEB"#, r#"Acid does the cutting"#),
            ("DEVELOP", r#"PEB"#, r#"Too short, too long"#),
            ("DEVELOP", r#"PEB"#, r#"Faster baking"#),
            ("DEVELOP", r#"DEVELOP"#, r#"Dissolving the exposed part"#),
            ("DEVELOP", r#"DEVELOP"#, r#"Swelling and collapse"#),
            ("DEVELOP", r#"DEVELOP"#, r#"On the track"#),
            ("DEVELOP", r#"RINSE"#, r#"Why thin lines fall over"#),
            ("DEVELOP", r#"RINSE"#, r#"Rinse chemistry fixes"#),
            ("DEVELOP", r#"RINSE"#, r#"Aspect ratio at High-NA"#),
            ("DEVELOP", r#"TO ETCH"#, r#"The resist is a stencil"#),
            ("DEVELOP", r#"TO ETCH"#, r#"Defects feed back"#),
            ("DEVELOP", r#"TO ETCH"#, r#"Pull-through"#),
            ("DEVELOP", r#"COOL"#, r#"Stopping the reaction"#),
            ("DEVELOP", r#"COOL"#, r#"Time adds blur"#),
            ("DEVELOP", r#"COOL"#, r#"Uniformity and speed"#),
            ("DEVELOP", r#"QUENCHER"#, r#"The brake on acid"#),
            ("DEVELOP", r#"QUENCHER"#, r#"The CAR trade-off"#),
            ("DEVELOP", r#"QUENCHER"#, r#"Metal-oxide contrast"#),
            ("DEVELOP", r#"TMAH dissolves"#, r#"What TMAH is"#),
            (
                "DEVELOP",
                r#"TMAH dissolves"#,
                r#"A small, conflicting market"#,
            ),
            ("DEVELOP", r#"TMAH dissolves"#, r#"Who supplies it"#),
            ("DEVELOP", r#"Gaussian blur"#, r#"The blur formula"#),
            ("DEVELOP", r#"Gaussian blur"#, r#"Worked values"#),
            ("DEVELOP", r#"Gaussian blur"#, r#"If baking were instant"#),
            ("DEVELOP", r#"HOT PLATE"#, r#"The bake module"#),
            ("DEVELOP", r#"HOT PLATE"#, r#"Who builds it"#),
            ("DEVELOP", r#"HOT PLATE"#, r#"Pace of the scanner"#),
            ("DEVELOP", r#"CHUCK"#, r#"Develop module hardware"#),
            ("DEVELOP", r#"CHUCK"#, r#"Uniform dissolution"#),
            ("DEVELOP", r#"CHUCK"#, r#"Pull-through for TEL"#),
            (
                "DEVELOP",
                r#"Metal-oxide resists"#,
                r#"More photons, rougher edges"#,
            ),
            (
                "DEVELOP",
                r#"Metal-oxide resists"#,
                r#"Stochastics at High-NA"#,
            ),
            (
                "DEVELOP",
                r#"Metal-oxide resists"#,
                r#"Suppliers and the licence deal"#,
            ),
            ("DEVELOP", r#"Lam DRY RESIST"#, r#"What dry resist is"#),
            ("DEVELOP", r#"Lam DRY RESIST"#, r#"Claimed benefits"#),
            ("DEVELOP", r#"Lam DRY RESIST"#, r#"Who gains, who loses"#),
            ("DEVELOP", r#"Chokepoints"#, r#"Tracks and chemicals"#),
            ("DEVELOP", r#"Chokepoints"#, r#"Risks"#),
            ("DEVELOP", r#"Chokepoints"#, r#"One cluster"#),
            ("ETCH", r#"HARD MASK"#, r#"Resist is too soft"#),
            ("ETCH", r#"HARD MASK"#, r#"Selectivity caps depth"#),
            ("ETCH", r#"HARD MASK"#, r#"Layers drive etch demand"#),
            ("ETCH", r#"IGNITE"#, r#"From neutral gas to plasma"#),
            ("ETCH", r#"IGNITE"#, r#"RIE versus ICP"#),
            ("ETCH", r#"IGNITE"#, r#"Drift and chamber matching"#),
            ("ETCH", r#"RADICALS"#, r#"The chemical half"#),
            ("ETCH", r#"RADICALS"#, r#"Gas choices by film"#),
            ("ETCH", r#"RADICALS"#, r#"When radicals are the point"#),
            ("ETCH", r#"ION-ASSISTED"#, r#"Ions make it vertical"#),
            ("ETCH", r#"ION-ASSISTED"#, r#"Source power and bias"#),
            ("ETCH", r#"ION-ASSISTED"#, r#"Deep holes starve for ions"#),
            ("ETCH", r#"SIDEWALL"#, r#"The protective film"#),
            ("ETCH", r#"SIDEWALL"#, r#"A balancing act"#),
            ("ETCH", r#"SIDEWALL"#, r#"Cryo changes the balance"#),
            ("ETCH", r#"STRIP"#, r#"Remove the helpers"#),
            ("ETCH", r#"STRIP"#, r#"Why etch and clean are bundled"#),
            ("ETCH", r#"STRIP"#, r#"Yield risks in strip"#),
            ("ETCH", r#"SHOWERHEAD"#, r#"Even gas delivery"#),
            ("ETCH", r#"SHOWERHEAD"#, r#"A consumable part"#),
            ("ETCH", r#"SHOWERHEAD"#, r#"Chamber design differentiates"#),
            ("ETCH", r#"PLASMA:"#, r#"Three species"#),
            ("ETCH", r#"PLASMA:"#, r#"The sheath"#),
            ("ETCH", r#"PLASMA:"#, r#"Why ICP replaced RIE"#),
            ("ETCH", r#"ESC"#, r#"Holding and cooling the wafer"#),
            ("ETCH", r#"ESC"#, r#"Cryo etch demands more"#),
            ("ETCH", r#"ESC"#, r#"Failure modes"#),
            ("ETCH", r#"cathode"#, r#"The bottom electrode"#),
            ("ETCH", r#"cathode"#, r#"Bias is the deep-hole lever"#),
            ("ETCH", r#"cathode"#, r#"Pull from NAND and HBM"#),
            ("ETCH", r#"Lam Cryo 3.0"#, r#"What it is"#),
            ("ETCH", r#"Lam Cryo 3.0"#, r#"Why NAND needs it"#),
            ("ETCH", r#"Lam Cryo 3.0"#, r#"Risk"#),
            (
                "ETCH",
                r#"NAND channel hole"#,
                r#"A very deep, very thin hole"#,
            ),
            ("ETCH", r#"NAND channel hole"#, r#"How holes fail"#),
            ("ETCH", r#"NAND channel hole"#, r#"Why AI cares"#),
            ("ETCH", r#"aspect ratio"#, r#"Depth over width"#),
            ("ETCH", r#"aspect ratio"#, r#"Why depth is hard"#),
            ("ETCH", r#"aspect ratio"#, r#"Industry responses"#),
            ("ETCH", r#"ALE"#, r#"Two self-limiting steps"#),
            ("ETCH", r#"ALE"#, r#"Numbers from simulation"#),
            ("ETCH", r#"ALE"#, r#"Where it is used"#),
            ("ETCH", r#"China"#, r#"Lam's biggest region"#),
            ("ETCH", r#"China"#, r#"Who is buying"#),
            ("ETCH", r#"China"#, r#"Open questions"#),
            (
                "ETCH",
                r#"Etch+clean 22"#,
                r#"Share of wafer-fab equipment"#,
            ),
            ("ETCH", r#"Etch+clean 22"#, r#"Why it swings"#),
            ("ETCH", r#"Etch+clean 22"#, r#"Investor read"#),
            ("ETCH", r#"Tokyo Electron"#, r#"Number two in etch"#),
            ("ETCH", r#"Tokyo Electron"#, r#"Estimated share"#),
            ("ETCH", r#"Tokyo Electron"#, r#"Competitive map"#),
            ("ETCH", r#"Lam Research (LRCX)"#, r#"The pure play"#),
            ("ETCH", r#"Lam Research (LRCX)"#, r#"Product pillars"#),
            ("ETCH", r#"Lam Research (LRCX)"#, r#"Risks"#),
            ("IMPLANT", r#"SOURCE"#, r#"Making ions"#),
            ("IMPLANT", r#"SOURCE"#, r#"Which gas for which dopant"#),
            ("IMPLANT", r#"SOURCE"#, r#"Source sets throughput"#),
            ("IMPLANT", r#"EXTRACT"#, r#"Pulling ions out"#),
            ("IMPLANT", r#"EXTRACT"#, r#"Space charge limit"#),
            ("IMPLANT", r#"EXTRACT"#, r#"Failure modes"#),
            ("IMPLANT", r#"MASS"#, r#"Bending by mass"#),
            ("IMPLANT", r#"MASS"#, r#"Many species leave the source"#),
            ("IMPLANT", r#"MASS"#, r#"Why implant has no substitute"#),
            ("IMPLANT", r#"ACCEL"#, r#"Energy sets depth"#),
            ("IMPLANT", r#"ACCEL"#, r#"Energy ranges by class"#),
            ("IMPLANT", r#"ACCEL"#, r#"Why Axcelis cares"#),
            ("IMPLANT", r#"SCAN +"#, r#"Spreading the beam evenly"#),
            ("IMPLANT", r#"SCAN +"#, r#"Dose is current times time"#),
            ("IMPLANT", r#"SCAN +"#, r#"Tilt and shadowing"#),
            ("IMPLANT", r#"ANNEAL"#, r#"Repair and activate"#),
            ("IMPLANT", r#"ANNEAL"#, r#"Heat versus diffusion"#),
            ("IMPLANT", r#"ANNEAL"#, r#"Thermal budget"#),
            ("IMPLANT", r#"ANALYZER"#, r#"A single-species beam"#),
            ("IMPLANT", r#"ANALYZER"#, r#"Resolution and vacuum"#),
            ("IMPLANT", r#"ANALYZER"#, r#"Transmission and tool lineup"#),
            ("IMPLANT", r#"Faraday cup"#, r#"Counting charge"#),
            ("IMPLANT", r#"Faraday cup"#, r#"Dose is the spec"#),
            ("IMPLANT", r#"Faraday cup"#, r#"Failure modes"#),
            ("IMPLANT", r#"channeling"#, r#"Open corridors in silicon"#),
            ("IMPLANT", r#"channeling"#, r#"Two fixes"#),
            ("IMPLANT", r#"channeling"#, r#"The normal profile"#),
            ("IMPLANT", r#"high current"#, r#"Heavy dose, low energy"#),
            ("IMPLANT", r#"high current"#, r#"The scaling pain"#),
            ("IMPLANT", r#"high current"#, r#"Three classes"#),
            ("IMPLANT", r#"Applied Mat."#, r#"Market share"#),
            ("IMPLANT", r#"Applied Mat."#, r#"Share over time"#),
            (
                "IMPLANT",
                r#"Applied Mat."#,
                r#"Why it is not the stock driver"#,
            ),
            ("IMPLANT", r#"Axcelis"#, r#"Almost pure implant"#),
            ("IMPLANT", r#"Axcelis"#, r#"The Veeco merger"#),
            ("IMPLANT", r#"Axcelis"#, r#"SiC position"#),
            (
                "IMPLANT",
                r#"SEN (Sumitomo Heavy 6302.T)"#,
                r#"A 50/50 joint venture"#,
            ),
            (
                "IMPLANT",
                r#"SEN (Sumitomo Heavy 6302.T)"#,
                r#"What is not confirmed"#,
            ),
            (
                "IMPLANT",
                r#"SEN (Sumitomo Heavy 6302.T)"#,
                r#"Why Japan matters"#,
            ),
            ("IMPLANT", r#"laser anneal"#, r#"Surface-only heating"#),
            ("IMPLANT", r#"laser anneal"#, r#"Shorter and hotter"#),
            ("IMPLANT", r#"laser anneal"#, r#"Failure modes"#),
            ("CLEAN", r#"ORGANICS"#, r#"SPM: the hot first step"#),
            ("CLEAN", r#"ORGANICS"#, r#"Side effects"#),
            ("CLEAN", r#"ORGANICS"#, r#"Step counts rise with layers"#),
            ("CLEAN", r#"RINSE"#, r#"DI water between every chemistry"#),
            ("CLEAN", r#"RINSE"#, r#"Water quality"#),
            ("CLEAN", r#"RINSE"#, r#"Rinse time costs throughput"#),
            ("CLEAN", r#"OXIDE"#, r#"DHF: strip native oxide"#),
            ("CLEAN", r#"OXIDE"#, r#"A clean but reactive surface"#),
            ("CLEAN", r#"OXIDE"#, r#"Order and failure modes"#),
            ("CLEAN", r#"PARTICLES"#, r#"SC1 undercuts particles"#),
            ("CLEAN", r#"PARTICLES"#, r#"Charge repulsion"#),
            ("CLEAN", r#"PARTICLES"#, r#"Roughness versus removal"#),
            ("CLEAN", r#"METALS"#, r#"SC2 turns metals into chlorides"#),
            ("CLEAN", r#"METALS"#, r#"The quiet killer"#),
            ("CLEAN", r#"METALS"#, r#"Modern variants"#),
            ("CLEAN", r#"DRY"#, r#"Water must leave cleanly"#),
            ("CLEAN", r#"DRY"#, r#"Supercritical CO2"#),
            ("CLEAN", r#"DRY"#, r#"Batch versus single-wafer drying"#),
            (
                "CLEAN",
                r#"chem nozzle arm"#,
                r#"Dispensing onto a spinning wafer"#,
            ),
            (
                "CLEAN",
                r#"chem nozzle arm"#,
                r#"Fresh chemistry each wafer"#,
            ),
            ("CLEAN", r#"chem nozzle arm"#, r#"Vendors"#),
            (
                "CLEAN",
                r#"megasonic transducer"#,
                r#"Sound that shears particles"#,
            ),
            ("CLEAN", r#"megasonic transducer"#, r#"A narrow window"#),
            ("CLEAN", r#"megasonic transducer"#, r#"Pressure points"#),
            ("CLEAN", r#"splash guard"#, r#"Bowl, rings and drains"#),
            ("CLEAN", r#"splash guard"#, r#"Hazardous chemistry"#),
            ("CLEAN", r#"splash guard"#, r#"Cross-contamination"#),
            (
                "CLEAN",
                r#"Marangoni"#,
                r#"The meniscus pulls lines together"#,
            ),
            ("CLEAN", r#"Marangoni"#, r#"Methods compared"#),
            ("CLEAN", r#"Marangoni"#, r#"Why scCO2 is not everywhere"#),
            (
                "CLEAN",
                r#"BATCH WET BENCH"#,
                r#"Batch versus single-wafer"#,
            ),
            ("CLEAN", r#"BATCH WET BENCH"#, r#"SCREEN's position"#),
            ("CLEAN", r#"BATCH WET BENCH"#, r#"Drift to single-wafer"#),
            ("CLEAN", r#"Etch + clean"#, r#"A slice of WFE"#),
            ("CLEAN", r#"Etch + clean"#, r#"Who sells it"#),
            ("CLEAN", r#"Etch + clean"#, r#"Why it grows with AI"#),
            ("CLEAN", r#"SC1"#, r#"Recipe spread"#),
            ("CLEAN", r#"SC1"#, r#"Self-limiting chemistry"#),
            ("CLEAN", r#"SC1"#, r#"Failure modes"#),
            (
                "CLEAN",
                r#"Report C 2023"#,
                r#"Why the market size is uncertain"#,
            ),
            ("CLEAN", r#"Report C 2023"#, r#"Cross-checks"#),
            ("CLEAN", r#"Report C 2023"#, r#"Better anchors"#),
        ];
        for (p, c, s) in all {
            let v = lookup(p, c, s).unwrap_or_else(|| panic!("missing {p}/{c}/{s}"));
            check(&v, &format!("{p}/{c}/{s}"));
        }
    }
}
