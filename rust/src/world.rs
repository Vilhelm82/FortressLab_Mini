//! The world in three dimensions.
//!
//! Columns of typed blocks, not a heightmap — the design needs subsurface
//! works, and a heightmap cannot express a tunnel.
//!
//! ```text
//! z = 0      bedrock / earth, solid unless excavated
//! z = 1..n   what is built; a wall 2 high fills z=1 and z=2
//! a man      stands in the lowest air cell above a solid one
//! his eye    is at his own z
//! ```
//!
//! Sound moves through air in 26 directions and pays to cross material, so
//! it goes over a low wall or along a corridor with no rule for either.
//! Men move on the level in 8 directions, and change level only by a stair.

use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap};

pub type Cell = (i32, i32, i32);

#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub enum Material {
    Earth,
    Stone,
    Timber,
    /// Solid like anything else — it stops sight and sound identically — but
    /// a man may change one level onto or off it. One stair lifts you one
    /// level; a second needs something solid beneath it.
    Stair,
}

impl Material {
    pub fn glyph(self) -> char {
        match self {
            Material::Earth => '.',
            Material::Stone => '#',
            Material::Timber => '=',
            Material::Stair => '/',
        }
    }
}

/// Eight compass steps.
pub const NB8: [(i32, i32); 8] = [
    (-1, -1), (-1, 0), (-1, 1), (0, -1),
    (0, 1), (1, -1), (1, 0), (1, 1),
];

/// f64 ordered for the heap. Costs here are finite and non-NaN by
/// construction; impassable edges are skipped rather than pushed.
#[derive(Copy, Clone, PartialEq)]
struct Cost(f64);
impl Eq for Cost {}
impl Ord for Cost {
    fn cmp(&self, other: &Self) -> Ordering {
        other.0.total_cmp(&self.0) // reversed: BinaryHeap is a max-heap
    }
}
impl PartialOrd for Cost {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

pub struct World {
    pub w: i32,
    pub h: i32,
    pub depth: i32,
    solid: HashMap<Cell, Material>,
}

impl World {
    pub fn new(w: i32, h: i32, depth: i32) -> Self {
        let mut solid = HashMap::new();
        for x in 0..w {
            for y in 0..h {
                solid.insert((x, y, 0), Material::Earth);
            }
        }
        World { w, h, depth, solid }
    }

    pub fn empty(w: i32, h: i32, depth: i32) -> Self {
        World { w, h, depth, solid: HashMap::new() }
    }

    // --- editing ---------------------------------------------------------

    pub fn fill(&mut self, x: i32, y: i32, z0: i32, z1: i32, m: Material) {
        for z in z0..=z1 {
            self.solid.insert((x, y, z), m);
        }
    }

    pub fn excavate(&mut self, c: Cell) {
        self.solid.remove(&c);
    }

    pub fn material(&self, c: Cell) -> Option<Material> {
        self.solid.get(&c).copied()
    }

    pub fn in_bounds(&self, c: Cell) -> bool {
        c.0 >= 0 && c.0 < self.w && c.1 >= 0 && c.1 < self.h
            && c.2 >= -self.depth && c.2 <= self.depth
    }

    pub fn air(&self, c: Cell) -> bool {
        self.in_bounds(c) && !self.solid.contains_key(&c)
    }

    /// Highest solid z in a column; `None` if the column is all air.
    pub fn column_top(&self, x: i32, y: i32) -> Option<i32> {
        (-self.depth..=self.depth)
            .rev()
            .find(|&z| self.solid.contains_key(&(x, y, z)))
    }

    /// Where a man on this column stands: the air cell just above the
    /// highest solid block.
    pub fn stand(&self, x: i32, y: i32) -> Option<Cell> {
        let top = self.column_top(x, y)?;
        let c = (x, y, top + 1);
        if self.air(c) { Some(c) } else { None }
    }

    /// Air, with something solid directly beneath.
    pub fn standable(&self, c: Cell) -> bool {
        self.air(c) && !self.air((c.0, c.1, c.2 - 1))
    }

    pub fn on_stair(&self, c: Cell) -> bool {
        self.material((c.0, c.1, c.2 - 1)) == Some(Material::Stair)
    }

    /// Where a man standing at `c` may go next tick. Eight compass steps on
    /// the level, always. A change of one level is legal only when the
    /// HIGHER of the two standing cells rests on a stair.
    pub fn steps_from(&self, c: Cell) -> Vec<Cell> {
        if !self.standable(c) {
            return vec![];
        }
        let mut out = Vec::new();
        for (dx, dy) in NB8 {
            for dz in [0, 1, -1] {
                let n = (c.0 + dx, c.1 + dy, c.2 + dz);
                if !self.standable(n) {
                    continue;
                }
                if dz != 0 {
                    let higher = if n.2 > c.2 { n } else { c };
                    if !self.on_stair(higher) {
                        continue;
                    }
                }
                out.push(n);
                break; // nearest reachable level in this direction
            }
        }
        out
    }

    pub fn standing_cells(&self) -> Vec<Cell> {
        let mut out = Vec::new();
        for x in 0..self.w {
            for y in 0..self.h {
                for z in -self.depth..=self.depth {
                    let c = (x, y, z);
                    if self.standable(c) {
                        out.push(c);
                    }
                }
            }
        }
        out
    }

    // --- propagation -----------------------------------------------------

    /// Amplitude multiplier per cell for ONE band, by the loudest path.
    ///
    /// Sound does not take the shortest route; it takes the one that
    /// delivers the most energy. Dijkstra in -log(amplitude) space, per
    /// band, because decay and transmission both differ by band: the bass
    /// goes through walls, the specifier only round them.
    pub fn band_field(
        &self,
        src: Cell,
        step_decay: f64,
        tx: &HashMap<Material, f64>,
    ) -> HashMap<Cell, f64> {
        let step = -step_decay.ln();
        let wall_cost = |m: Material| -> f64 {
            match tx.get(&m) {
                Some(v) if *v > 0.0 => -v.ln(),
                _ => f64::INFINITY,
            }
        };

        let mut cost: HashMap<Cell, f64> = HashMap::new();
        let mut pq: BinaryHeap<(Cost, Cell)> = BinaryHeap::new();
        cost.insert(src, 0.0);
        pq.push((Cost(0.0), src));

        while let Some((Cost(c), cell)) = pq.pop() {
            if c > *cost.get(&cell).unwrap_or(&f64::INFINITY) {
                continue;
            }
            for dx in -1..=1 {
                for dy in -1..=1 {
                    for dz in -1..=1 {
                        if (dx, dy, dz) == (0, 0, 0) {
                            continue;
                        }
                        let n = (cell.0 + dx, cell.1 + dy, cell.2 + dz);
                        if !self.in_bounds(n) {
                            continue;
                        }
                        let w = match self.material(n) {
                            Some(m) => wall_cost(m),
                            None => 0.0,
                        };
                        if w.is_infinite() {
                            continue;
                        }
                        let nc = c + step + w;
                        if nc < *cost.get(&n).unwrap_or(&f64::INFINITY) {
                            cost.insert(n, nc);
                            pq.push((Cost(nc), n));
                        }
                    }
                }
            }
        }
        cost.into_iter().map(|(k, v)| (k, (-v).exp())).collect()
    }

    // --- sight -----------------------------------------------------------

    /// 3D line of sight, sampled along the segment. Height therefore
    /// matters: a man on a tower sees over a curtain that blinds one
    /// standing beside it.
    pub fn los(&self, a: Cell, b: Cell) -> bool {
        let n = (b.0 - a.0).abs().max((b.1 - a.1).abs()).max((b.2 - a.2).abs());
        if n == 0 {
            return true;
        }
        for i in 1..n {
            let t = i as f64 / n as f64;
            let c = (
                (a.0 as f64 + (b.0 - a.0) as f64 * t).round() as i32,
                (a.1 as f64 + (b.1 - a.1) as f64 * t).round() as i32,
                (a.2 as f64 + (b.2 - a.2) as f64 * t).round() as i32,
            );
            if c == a || c == b {
                continue;
            }
            if !self.air(c) {
                return false;
            }
        }
        true
    }

    // --- looking at it ---------------------------------------------------

    /// A side-on slice along one row: what you would see standing due south.
    pub fn section(&self, y: i32, z_top: i32, marks: &HashMap<Cell, char>) -> String {
        let mut out = String::new();
        for z in (0..=z_top).rev() {
            out.push_str(&format!("{:2} |", z));
            for x in 0..self.w {
                let c = (x, y, z);
                out.push(match marks.get(&c) {
                    Some(&m) => m,
                    None => self.material(c).map(|m| m.glyph()).unwrap_or(' '),
                });
            }
            out.push_str("|\n");
        }
        out.push_str(&format!("   +{}+\n    ", "-".repeat(self.w as usize)));
        for x in 0..self.w {
            out.push_str(&((x % 10).to_string()));
        }
        out
    }

    /// Looking down: the height of each column, or a man's mark.
    pub fn plan(&self, marks: &HashMap<Cell, char>) -> String {
        let flat: HashMap<(i32, i32), char> =
            marks.iter().map(|(c, &m)| ((c.0, c.1), m)).collect();
        let mut out = String::from("   ");
        for x in 0..self.w {
            out.push_str(&((x % 10).to_string()));
        }
        out.push('\n');
        for y in 0..self.h {
            out.push_str(&format!("{:2} ", y));
            for x in 0..self.w {
                if let Some(&m) = flat.get(&(x, y)) {
                    out.push(m);
                    continue;
                }
                out.push(match self.column_top(x, y) {
                    None | Some(0) => '.',
                    Some(t) => {
                        if self.material((x, y, t)) == Some(Material::Stair) {
                            '/'
                        } else {
                            char::from_digit(t as u32 % 10, 10).unwrap()
                        }
                    }
                });
            }
            out.push('\n');
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tx(stone: f64, timber: f64) -> HashMap<Material, f64> {
        HashMap::from([
            (Material::Earth, 0.0),
            (Material::Stone, stone),
            (Material::Timber, timber),
            (Material::Stair, stone),
        ])
    }

    /// A wall two high at x=6, with two stairs climbing to its walk.
    fn wall_and_stairs() -> World {
        let mut w = World::new(12, 3, 5);
        w.fill(6, 1, 1, 2, Material::Stone);
        w.fill(4, 1, 1, 1, Material::Stair);
        w.fill(5, 1, 1, 1, Material::Stone);
        w.fill(5, 1, 2, 2, Material::Stair);
        w
    }

    #[test]
    fn a_man_stands_on_top_of_what_is_beneath_him() {
        let w = wall_and_stairs();
        assert_eq!(w.stand(1, 1), Some((1, 1, 1)), "open ground");
        assert_eq!(w.stand(6, 1), Some((6, 1, 3)), "on the wall walk");
        assert_eq!(w.stand(4, 1), Some((4, 1, 2)), "on the first stair");
    }

    #[test]
    fn a_wall_cannot_be_climbed_without_stairs() {
        let mut w = World::new(12, 3, 5);
        w.fill(6, 1, 1, 2, Material::Stone);
        let from_ground = w.steps_from((5, 1, 1));
        assert!(!from_ground.contains(&(6, 1, 3)), "no scrambling up walls");
        assert!(from_ground.iter().all(|c| c.2 == 1), "all moves stay level");
    }

    #[test]
    fn one_stair_lifts_one_level_and_no_more() {
        let mut w = World::new(12, 3, 5);
        w.fill(6, 1, 1, 2, Material::Stone);
        w.fill(4, 1, 1, 1, Material::Stair);
        assert!(w.steps_from((3, 1, 1)).contains(&(4, 1, 2)), "up the stair");
        let top = w.steps_from((4, 1, 2));
        assert!(!top.contains(&(6, 1, 3)), "stuck at the top of one stair");
        assert!(top.contains(&(3, 1, 1)), "and can come back down");
    }

    #[test]
    fn two_stairs_reach_the_wall_walk() {
        let w = wall_and_stairs();
        assert!(w.steps_from((4, 1, 2)).contains(&(5, 1, 3)), "second stair");
        assert!(w.steps_from((5, 1, 3)).contains(&(6, 1, 3)), "onto the walk");
        assert_eq!(w.steps_from((6, 1, 3)), vec![(5, 1, 3)],
                   "and the only way off the walk is back down the stair");
    }

    #[test]
    fn height_blocks_sight_and_grants_it() {
        let mut w = World::new(12, 3, 5);
        w.fill(6, 1, 1, 2, Material::Stone);
        assert!(!w.los((1, 1, 1), (11, 1, 1)), "ground to ground is blocked");
        assert!(w.los((6, 1, 3), (11, 1, 1)), "from the wall walk it is not");
    }

    #[test]
    fn the_bass_crosses_stone_and_the_specifier_climbs_over_it() {
        let mut w = World::new(12, 3, 5);
        w.fill(6, 1, 1, 2, Material::Stone);
        let src = (11, 1, 1);
        let bass = w.band_field(src, 0.97, &tx(0.6, 0.9));
        let spec = w.band_field(src, 0.88, &tx(0.0, 0.5));
        let far = (1, 1, 1);
        assert!(bass[&far] > 0.0, "bass passes through the wall");
        assert!(spec.get(&far).copied().unwrap_or(0.0) > 0.0,
                "the specifier cannot cross stone, so it goes over the top");
        assert!(spec[&(6, 1, 3)] > spec[&far],
                "and it is loudest where the way over is shortest");
    }

    #[test]
    fn earth_stops_everything_so_the_ground_is_not_a_shortcut() {
        let w = World::new(8, 3, 4);
        let f = w.band_field((6, 1, 1), 0.97, &tx(0.6, 0.9));
        assert!(!f.contains_key(&(1, 1, 0)), "no sound inside the earth");
    }

    #[test]
    fn the_loudest_path_is_taken_not_the_shortest() {
        // A room with one door: the way round must beat the way through.
        let mut w = World::new(11, 7, 4);
        for x in 3..=7 {
            w.fill(x, 2, 1, 2, Material::Stone);
            w.fill(x, 5, 1, 2, Material::Stone);
        }
        for y in 2..=5 {
            w.fill(3, y, 1, 2, Material::Stone);
            w.fill(7, y, 1, 2, Material::Stone);
        }
        w.excavate((5, 5, 1));
        w.excavate((5, 5, 2)); // a doorway in the south wall
        let spec = w.band_field((5, 3, 1), 0.88, &tx(0.0, 0.5));
        let below_door = spec.get(&(5, 6, 1)).copied().unwrap_or(0.0);
        let behind_wall = spec.get(&(5, 1, 1)).copied().unwrap_or(0.0);
        assert!(below_door > behind_wall,
                "the doorway leaks; the wall opposite does not");
    }
}
