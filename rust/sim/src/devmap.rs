//! The development castle — one map, used throughout.
//!
//! A fixture, not a scenario. It exists so every subsystem is exercised
//! against the same geometry: stone and timber side by side, four heights, a
//! gate that opens into a cul-de-sac, a hollow keep, a postern, stairs to the
//! wall-walks, and open field to approach across.
//!
//! ```text
//! x 0-11    open field. The attacker's ground.
//! x 12      west curtain, MAIN GATE at y10-11.
//! x 13-17   the BARBICAN POCKET — a cul-de-sac. The gate opens into it and
//!           the only way out is north, over the top of the spur.
//! x 18      the spur, 1 high, y6-13, closed along y14.
//! x 19-32   the bailey.
//! x 26-30   the KEEP, hollow, 4 high, one door south at (28,12).
//!           The war room sits inside at (28,10).
//! x 24-31   on y19: TIMBER palisade — the one stretch that leaks detail.
//! corners   towers, 3 high. Curtain elsewhere 2 high.
//! stairs    two flights inside the west and east walls, so the garrison can
//!           actually reach its own wall-walks.
//! ```
//!
//! Regions are assigned by whoever designs a map, and there are UP TO twelve
//! — a small castle may use four and leave the rest of the address space
//! unused. The game assigns which fundamental each region receives.

use crate::world::{Material, World};

pub const W: i32 = 36;
pub const H: i32 = 22;
pub const DEPTH: i32 = 6;

pub const GATE_Y: (i32, i32) = (10, 11);
pub const POSTERN_X: i32 = 26;
pub const WAR_ROOM: (i32, i32, i32) = (28, 10, 1);
pub const KEEP_DOOR: (i32, i32) = (28, 12);
pub const SPUR_X: i32 = 18;
pub const SPUR_Y: (i32, i32) = (6, 13);
pub const CASTLE: (i32, i32, i32, i32) = (12, 2, 33, 19);
pub const PALISADE_X: (i32, i32) = (24, 31);

pub const CURTAIN_H: i32 = 2;
pub const TOWER_H: i32 = 3;
pub const KEEP_H: i32 = 4;

/// A named region of the map. The designer's division; the game tunes it.
pub struct Region {
    pub name: &'static str,
    /// One or more rectangles — real regions are not rectangles, and the
    /// west curtain is cut in two by its own gate.
    pub rects: &'static [(i32, i32, i32, i32)],
}

pub const REGIONS: &[Region] = &[
    Region { name: "field", rects: &[(0, 0, 11, 21)] },
    Region { name: "main-gate", rects: &[(12, 9, 12, 12)] },
    Region { name: "barbican", rects: &[(13, 3, 17, 13)] },
    Region { name: "west-curtain", rects: &[(12, 2, 12, 8), (12, 13, 12, 19)] },
    Region { name: "north-curtain", rects: &[(13, 2, 25, 2)] },
    Region { name: "postern", rects: &[(26, 2, 26, 2)] },
    Region { name: "east-curtain", rects: &[(33, 2, 33, 19)] },
    Region { name: "south-curtain", rects: &[(13, 19, 23, 19)] },
    Region { name: "palisade", rects: &[(24, 19, 31, 19)] },
    Region { name: "bailey-north", rects: &[(19, 3, 32, 7)] },
    Region { name: "bailey-south", rects: &[(19, 14, 32, 18)] },
    Region { name: "keep", rects: &[(26, 8, 30, 12)] },
];

/// A flight of stairs rising from ground to `top`, laid out along +x.
/// Each stair sits on the block below it, so the run takes `top` columns.
fn stair_flight(w: &mut World, x0: i32, y: i32, top: i32, dx: i32) {
    for i in 0..top {
        let x = x0 + i * dx;
        if i > 0 {
            w.fill(x, y, 1, i, Material::Stone); // something to stand the stair on
        }
        w.fill(x, y, i + 1, i + 1, Material::Stair);
    }
}

pub fn build() -> World {
    let mut w = World::new(W, H, DEPTH);
    let (x0, y0, x1, y1) = CASTLE;

    // north and south curtain
    for x in x0..=x1 {
        w.fill(x, y0, 1, CURTAIN_H, Material::Stone);
        let m = if x >= PALISADE_X.0 && x <= PALISADE_X.1 {
            Material::Timber
        } else {
            Material::Stone
        };
        w.fill(x, y1, 1, CURTAIN_H, m);
    }
    // west and east curtain
    for y in y0..=y1 {
        w.fill(x0, y, 1, CURTAIN_H, Material::Stone);
        w.fill(x1, y, 1, CURTAIN_H, Material::Stone);
    }
    // corner towers
    for (cx, cy) in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)] {
        w.fill(cx, cy, 1, TOWER_H, Material::Stone);
    }

    // gates: shut, so the castle is sealed until something is breached
    w.fill(POSTERN_X, y0, 1, CURTAIN_H, Material::Stone);
    for y in GATE_Y.0..=GATE_Y.1 {
        w.fill(x0, y, 1, CURTAIN_H, Material::Stone);
    }

    // the spur, and the wall closing the pocket
    for y in SPUR_Y.0..=SPUR_Y.1 {
        w.fill(SPUR_X, y, 1, 1, Material::Stone);
    }
    for x in (x0 + 1)..=SPUR_X {
        w.fill(x, SPUR_Y.1 + 1, 1, 1, Material::Stone);
    }

    // the keep: hollow, one door
    let (kx0, ky0, kx1, ky1) = (26, 8, 30, 12);
    for x in kx0..=kx1 {
        w.fill(x, ky0, 1, KEEP_H, Material::Stone);
        w.fill(x, ky1, 1, KEEP_H, Material::Stone);
    }
    for y in ky0..=ky1 {
        w.fill(kx0, y, 1, KEEP_H, Material::Stone);
        w.fill(kx1, y, 1, KEEP_H, Material::Stone);
    }
    for z in 1..=KEEP_H {
        w.excavate((KEEP_DOOR.0, KEEP_DOOR.1, z));
    }

    // stairs to the wall-walks, inside the bailey
    stair_flight(&mut w, 14, 4, CURTAIN_H, -1); // climbs west onto the curtain
    stair_flight(&mut w, 31, 16, CURTAIN_H, 1);  // climbs east onto the curtain

    // a step up from the curtain onto the towers, which stand a level higher.
    // Without these the towers are unreachable and their vantage is wasted.
    w.fill(x0, y0 + 1, CURTAIN_H + 1, CURTAIN_H + 1, Material::Stair);
    w.fill(x1, y1 - 1, CURTAIN_H + 1, CURTAIN_H + 1, Material::Stair);
    w
}

/// Cells of the main gate, for scenarios that force it open.
pub fn gate_cells() -> Vec<(i32, i32, i32)> {
    let mut out = Vec::new();
    for y in GATE_Y.0..=GATE_Y.1 {
        for z in 1..=CURTAIN_H {
            out.push((CASTLE.0, y, z));
        }
    }
    out
}
