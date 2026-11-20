// SHIP: the page's overview, a Blender scene (tools/pbr3d/blender/ship_overview.py, GLB
// tools/pbr3d/assets/ship_overview.glb). One diorama left to right: an ODM assembly line, a liquid-cooled
// rack with its coolant units, a coolant loop, a barrier gate on the road to the buyer, a crated rack on a
// truck and the data hall at the far end; gold beads ride the product flow, cyan beads the coolant.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/ship_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match ship_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("assembly: the ODM builds the board", BEAT_MS)
        .note(
            "After final test, the chips go into physical assembly. An ODM (original design manufacturer, a contract maker such as Foxconn, Quanta or Wistron) mounts the tested GPU and CPU modules onto boards. Board assembly is where a tested module first meets the rest of the server.",
            "A conveyor carries a green board past the camera. Two dark GPU modules with gold lids and a grey CPU module sit on it. Gold beads of product flow along the belt from the left.",
        )
        .detail(
            "The ODM does the physical assembly.",
            &["ODMs: Foxconn, Quanta, Wistron", "Tested modules go on boards, then into trays"],
        ),
    Beat::new("who builds: ODM or OEM", BEAT_MS)
        .note(
            "Two kinds of company put a GPU into a working server. An ODM does rack-scale engineering and physical assembly, often for hyperscalers. An OEM such as Dell, HPE or Supermicro designs the chassis, cooling, power delivery and firmware, and sells the system under its own brand and warranty.",
            "A wide shot: the assembly line on the left, the tall rack in the middle and its coolant units beside it. Tags mark the ODM's assembly and the OEM's design and sale.",
        )
        .detail(
            "ODMs still build most servers, but OEMs are gaining.",
            &["ODM Direct: 50.2% of server market in Q1 2026 (64.1% a year earlier)", "OEMs: Dell, HPE, Supermicro, Lenovo"],
        ),
    Beat::new("one rack: 72 GPUs as one", BEAT_MS)
        .note(
            "The NVIDIA GB200 NVL72 is built and sold as one liquid-cooled rack: 72 Blackwell GPUs and 36 Grace CPUs, linked by NVLink through the rack. Its 130 TB/s of NVLink bandwidth is what lets the rack act as one large GPU.",
            "A dark rack, front view: trays stacked in rows, the middle nine switch trays green and the rest grey compute trays with green status lights. Gold beads run up the front, and tags mark the GPU and CPU counts.",
        )
        .detail(
            "One rack, 72 GPUs.",
            &["72 Blackwell GPUs, 36 Grace CPUs (NVIDIA)", "130 TB/s NVLink bandwidth (NVIDIA)", "Liquid-cooled, rack-scale design (NVIDIA)"],
        ),
    Beat::new("tests: leaks and heat before shipping", BEAT_MS)
        .note(
            "Before a rack leaves the factory it is leak-checked and run under load in its liquid loop. The fittings and manifolds are the weak point: during the ramp, suppliers spent months fixing overheating and leaks in GB200 racks, and quick-connect fittings leaked despite factory stress tests.",
            "Cyan beads of coolant circle the rack's pipe loop: out of the right coolant unit, up the side, across the top and down the left. Tags mark the loop, the connectors and the tests.",
        )
        .detail(
            "Leaks were the ramp problem.",
            &["Months spent on leaks and overheating (Tom's Hardware)", "Quick-connect fittings leaked despite factory stress tests (Tom's Hardware)"],
        ),
    Beat::new("export: a licence for advanced chips", BEAT_MS)
        .note(
            "Advanced AI chips are export-controlled. In January 2026 the Commerce Department (BIS) moved licence review for Nvidia H200 and AMD MI325X chips bound for China to case-by-case. The conditions include customer screening, independent third-party testing in the US, and no cut to the supply available to US customers. The Biden-era AI diffusion rule was rescinded in May 2025.",
            "A road runs left to right past a red barrier gate and a booth at the gate. Tags mark the licence review and its conditions.",
        )
        .detail(
            "A licence still comes first for China.",
            &["BIS, 13 Jan 2026: case-by-case review for H200 and MI325X", "Conditions: customer screening, US third-party testing", "AI diffusion rule rescinded, May 2025"],
        ),
    Beat::new("ship: crated rack, by truck", BEAT_MS)
        .note(
            "The finished rack is crated and moved by truck to the buyer's site, usually a data center that already has power and liquid cooling ready for it. This is the last step of the chain: the buyer's own data hall takes the rack from the factory.",
            "A flatbed truck carries a wooden crate with a rack inside, down the road away from the gate and toward a grey data hall at the far end. Gold beads of product run along the road.",
        )
        .detail(
            "Shipping ends at the buyer's dock.",
            &["Buyers: hyperscalers, clouds, enterprises", "Site needs power and cooling first (see POWER)"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "SHIP overview");
        assert!(s.zooms().is_empty());
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "SHIP overview");
    }
}
