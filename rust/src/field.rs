//! The resonance field.
//!
//! Orders are performances, not prose. A location is tuned; units hear it,
//! harmonise toward it, and act on what degrades their own song. Everything
//! here is a pure function of position — nothing is cached across a tick,
//! because emitters move.

use std::collections::HashMap;

use crate::balance::*;
use crate::world::{Cell, World};

/// Twelve chromatic steps. A region is a step; a post is a diatonic degree
/// above it, voiced in the octave above the stone cutoff.
pub const SEMI: f64 = 1.059_463_094_359_295_3; // 2^(1/12)
/// The six non-root degrees of a seven-note scale.
pub const DEGREES: [i32; 6] = [2, 4, 5, 7, 9, 11];

/// A note: which octave it sits in, and its exact frequency.
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct Note {
    pub layer: Layer,
    pub hz: f64,
}

impl Note {
    fn at(layer: Layer, semitone: i32) -> Note {
        let hz = BASE_HZ * layer.octave() * SEMI.powi(semitone);
        Note { layer, hz: (hz * 100.0).round() / 100.0 }
    }
    pub fn same(&self, other: &Note) -> bool {
        self.layer == other.layer && (self.hz - other.hz).abs() < 1e-9
    }
}

/// The region's fundamental. Twelve of them, one per addressable region.
pub fn region_root(region: i32) -> Note {
    Note::at(Layer::Loc, region.rem_euclid(12))
}

/// The sub-location within a region: a diatonic degree in the octave above
/// the stone cutoff, so stone hides which post while leaving the region
/// audible.
pub fn dyad_specifier(region: i32, degree_ix: usize) -> Note {
    Note::at(Layer::Spec, (region + DEGREES[degree_ix]).rem_euclid(12))
}

/// A company leader sings the octave between the location and the specifier.
pub fn leader_note(region: i32) -> Note {
    Note::at(Layer::Lead, region.rem_euclid(12))
}

/// An extension: a condition or a tactic layered above the address.
pub fn extension(region: i32, degree_ix: usize) -> Note {
    Note::at(Layer::Ext, (region + DEGREES[degree_ix]).rem_euclid(12))
}

/// Anything that sings: a tuned location, a leader, a unit.
#[derive(Clone, Debug)]
pub struct Emitter {
    pub pos: Cell,
    pub notes: Vec<Note>,
    /// +1 Home, -1 Away. Opposed emitters are 180 degrees out of phase.
    pub sign: f64,
    /// Voice gain. A commander may gate any unit's dB; the perception beam
    /// is NOT attenuated by it — stealth costs acoustic resolution, not
    /// sight.
    pub db: f64,
    /// Amplitude scales with the strength of numbers.
    pub numbers: f64,
    pub facing: (i32, i32),
}

impl Emitter {
    pub fn new(pos: Cell, notes: Vec<Note>) -> Emitter {
        Emitter { pos, notes, sign: 1.0, db: 1.0, numbers: 1.0, facing: (1, 0) }
    }
    pub fn away(mut self) -> Emitter { self.sign = -1.0; self }
    pub fn db(mut self, v: f64) -> Emitter { self.db = v; self }
    pub fn numbers(mut self, v: f64) -> Emitter { self.numbers = v; self }
    pub fn facing(mut self, f: (i32, i32)) -> Emitter { self.facing = f; self }
}

/// What a unit notices, and by which channel.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Channels {
    /// Own beam. The strongest channel: directional, line of sight, in cone.
    pub looking: f64,
    /// Destructive interference. Degrades performance and navigation both.
    pub interference: f64,
    /// Omnidirectional wave, weighted by angle off centre, subject to
    /// masking by louder voices.
    pub hearing: f64,
    /// Being looked at. The weakest channel, and silent at 180 degrees.
    pub being_looked_at: f64,
}

pub struct Field<'a> {
    pub world: &'a World,
    pub emitters: Vec<Emitter>,
    bands: HashMap<(Cell, Layer), HashMap<Cell, f64>>,
}

impl<'a> Field<'a> {
    pub fn new(world: &'a World, emitters: Vec<Emitter>) -> Field<'a> {
        Field { world, emitters, bands: HashMap::new() }
    }

    fn band(&mut self, src: Cell, layer: Layer) -> &HashMap<Cell, f64> {
        self.bands.entry((src, layer)).or_insert_with(|| {
            world_band(self.world, src, layer)
        })
    }

    /// Amplitude of one emitter's note at a cell.
    pub fn amp(&mut self, e: &Emitter, n: &Note, at: Cell) -> f64 {
        let base = e.db * e.numbers * n.layer.weight();
        match self.band(e.pos, n.layer).get(&at) {
            Some(m) => base * m,
            None => 0.0,
        }
    }

    /// The signed spectrum at a cell. Opposed emitters subtract: where their
    /// peaks align they cancel, and that loss of harmonic content IS a
    /// unit's perception.
    pub fn hear(&mut self, at: Cell) -> Vec<(Note, f64)> {
        let ems = self.emitters.clone();
        let mut out: Vec<(Note, f64)> = Vec::new();
        for e in &ems {
            for n in &e.notes {
                let a = self.amp(e, n, at);
                if a <= 0.0 {
                    continue;
                }
                match out.iter_mut().find(|(m, _)| m.same(n)) {
                    Some((_, v)) => *v += e.sign * a,
                    None => out.push((*n, e.sign * a)),
                }
            }
        }
        out
    }

    pub fn band_at(&mut self, e: &Emitter, n: &Note, at: Cell) -> f64 {
        self.amp(e, n, at).abs()
    }

    // --- perception ------------------------------------------------------

    /// Angle between where an observer faces and where something is.
    /// 0 is dead ahead, pi is directly behind.
    pub fn angle_off_facing(o: &Emitter, target: Cell) -> f64 {
        let v = (target.0 - o.pos.0, target.1 - o.pos.1);
        if v == (0, 0) {
            return 0.0;
        }
        let a = (v.1 as f64).atan2(v.0 as f64)
            - (o.facing.1 as f64).atan2(o.facing.0 as f64);
        let mut a = a;
        while a > std::f64::consts::PI { a -= 2.0 * std::f64::consts::PI; }
        while a < -std::f64::consts::PI { a += 2.0 * std::f64::consts::PI; }
        a.abs()
    }

    pub fn channels(&mut self, observer: &Emitter, target: &Emitter) -> Channels {
        let d = ((target.pos.0 - observer.pos.0).abs())
            .max((target.pos.1 - observer.pos.1).abs())
            .max(1) as f64;

        // Looking: a directional beam. Height is in the coordinates, so a man
        // on a tower sees over a curtain that blinds one beside it.
        let in_cone = Field::angle_off_facing(observer, target.pos) <= BEAM_HALFANGLE;
        let seen = in_cone && d <= BEAM_RANGE
            && self.world.los(observer.pos, target.pos);
        let looking = if seen { 4.0 / d } else { 0.0 };

        // Interference: only on shared bands. No shared song, no cancellation.
        let mut interference = 0.0;
        for n in observer.notes.clone() {
            if target.notes.iter().any(|m| m.same(&n)) {
                interference += self.amp(target, &n, observer.pos).abs();
            }
        }
        interference *= 3.0;

        // Hearing: omnidirectional, weighted by angle, masked by louder
        // voices. A singer subtracts his own — echolocation already needs him
        // to know his own voice — and the target is signal, not noise.
        let raw: f64 = target.notes.clone().iter()
            .map(|n| self.amp(target, n, observer.pos).abs()).sum();
        let ems = self.emitters.clone();
        let mut ambient = 0.0;
        for e in &ems {
            if std::ptr::eq(e as *const _, observer as *const _) { continue; }
            if e.pos == observer.pos || e.pos == target.pos { continue; }
            for n in &e.notes {
                ambient += self.amp(e, n, observer.pos).abs();
            }
        }
        let audible = raw > HEAR_FLOOR.max(MASK_RATIO * ambient.max(0.0));
        let angle = Field::angle_off_facing(observer, target.pos);
        let hearing = if audible {
            raw * (0.25 + 0.75 * (angle / 2.0).cos().powi(2)) * 2.0
        } else {
            0.0
        };

        // Being looked at: felt only from inside the target's own cone, so
        // silent when he faces away.
        let beam_on_me = Field::angle_off_facing(target, observer.pos);
        let felt = if beam_on_me <= BEAM_HALFANGLE && d <= BEAM_RANGE
            && self.world.los(target.pos, observer.pos)
        {
            0.5 * beam_on_me.cos().max(0.0)
        } else {
            0.0
        };

        Channels { looking, interference, hearing, being_looked_at: felt }
    }

    /// The stronger cancellation source is a unit's offensive priority.
    pub fn priority_target(&mut self, unit: &Emitter, enemies: &[Emitter]) -> Option<usize> {
        let mut best: Option<(f64, usize)> = None;
        for (i, e) in enemies.iter().enumerate() {
            let s = self.channels(unit, e).interference;
            if s > 0.0 && best.map_or(true, |(b, _)| s > b) {
                best = Some((s, i));
            }
        }
        best.map(|(_, i)| i)
    }

    // --- echolocation ----------------------------------------------------

    /// A unit sings its own part and reads what comes back. How a bat
    /// navigates a cave: the location that answers loudest is the one it
    /// wants, and an empty post is not silent — it is unexcited.
    pub fn ping(&mut self, unit: &Emitter, loc: &Emitter) -> (f64, Vec<Layer>) {
        let shared: Vec<Note> = unit.notes.iter()
            .filter(|n| loc.notes.iter().any(|m| m.same(n)))
            .copied().collect();
        let mut strength = 0.0;
        let mut layers = Vec::new();
        for n in shared {
            let m = match self.band(unit.pos, n.layer).get(&loc.pos) {
                Some(v) => *v,
                None => continue,
            };
            let a = unit.db * n.layer.weight() * m * m; // out and back
            if a > ECHO_FLOOR {
                strength += a;
                if !layers.contains(&n.layer) {
                    layers.push(n.layer);
                }
            }
        }
        (strength, layers)
    }

    /// Which of these locations answers this unit best.
    pub fn navigate_target(&mut self, unit: &Emitter, locs: &[Emitter]) -> Option<usize> {
        let mut best: Option<(f64, usize)> = None;
        for (i, l) in locs.iter().enumerate() {
            let (s, _) = self.ping(unit, l);
            if s > 0.0 && best.map_or(true, |(b, _)| s > b) {
                best = Some((s, i));
            }
        }
        best.map(|(_, i)| i)
    }

    /// One step by ear alone: no map, no pathfinding.
    ///
    /// The specifier is the primary vector — it crosses no stone, so it
    /// reaches a unit only along routes that are actually walkable, and its
    /// gradient points back the way it came. Where neighbours answer
    /// equally, the root breaks the tie: it penetrates stone and holds a
    /// constant bearing on the region. Hearing neither means standing still.
    pub fn step_by_ear(&mut self, from: Cell, src: &Emitter) -> Option<Cell> {
        let cands = self.world.steps_from(from);
        if cands.is_empty() {
            return None;
        }
        let spec: Vec<Note> = src.notes.iter()
            .filter(|n| n.layer == Layer::Spec).copied().collect();
        let root: Vec<Note> = src.notes.iter()
            .filter(|n| n.layer == Layer::Loc).copied().collect();

        let score = |c: Cell, ns: &[Note], f: &mut Field| -> f64 {
            ns.iter().map(|n| f.amp(src, n, c).abs()).sum()
        };

        if !spec.is_empty() {
            let here = score(from, &spec, self);
            let scored: Vec<(f64, Cell)> = cands.iter()
                .map(|&c| (score(c, &spec, self), c)).collect();
            let best = scored.iter().fold(f64::NEG_INFINITY, |a, (s, _)| a.max(*s));
            if best > here + 1e-12 {
                let top: Vec<Cell> = scored.iter()
                    .filter(|(s, _)| (s - best).abs() <= 1e-12)
                    .map(|(_, c)| *c).collect();
                if top.len() == 1 || root.is_empty() {
                    return Some(top[0]);
                }
                let mut pick = top[0];
                let mut bestr = f64::NEG_INFINITY;
                for c in top {
                    let r = score(c, &root, self);
                    if r > bestr { bestr = r; pick = c; }
                }
                return Some(pick);
            }
        }
        // Bass only: a bearing, not a route.
        if root.is_empty() {
            return None;
        }
        let here = score(from, &root, self);
        let mut pick = None;
        let mut best = here + 1e-12;
        for c in cands {
            let r = score(c, &root, self);
            if r > best { best = r; pick = Some(c); }
        }
        pick
    }

    // --- routing ---------------------------------------------------------

    /// Least detection is the routing preference of ALL units (ruled), which
    /// is what makes a stealth kill a property of the ground rather than a
    /// coded behaviour.
    pub fn least_detection_route(
        &mut self,
        start: Cell,
        goal: Cell,
        watchers: &[Emitter],
    ) -> Vec<Cell> {
        use std::collections::BinaryHeap;
        let cells = self.world.standing_cells();
        let mut cost: HashMap<Cell, f64> = HashMap::new();
        for &c in &cells {
            let mut det = 0.0;
            for w in watchers {
                let d = ((c.0 - w.pos.0).abs()).max((c.1 - w.pos.1).abs()).max(1) as f64;
                if d <= BEAM_RANGE
                    && Field::angle_off_facing(w, c) < BEAM_HALFANGLE
                    && self.world.los(w.pos, c)
                {
                    det += 4.0 / d;
                }
            }
            cost.insert(c, 1.0 + LAMBDA_OBS * det * 50.0);
        }

        #[derive(PartialEq)]
        struct Q(f64, Cell);
        impl Eq for Q {}
        impl Ord for Q {
            fn cmp(&self, o: &Self) -> std::cmp::Ordering { o.0.total_cmp(&self.0) }
        }
        impl PartialOrd for Q {
            fn partial_cmp(&self, o: &Self) -> Option<std::cmp::Ordering> { Some(self.cmp(o)) }
        }

        let mut dist: HashMap<Cell, f64> = HashMap::from([(start, 0.0)]);
        let mut prev: HashMap<Cell, Cell> = HashMap::new();
        let mut pq = BinaryHeap::from([Q(0.0, start)]);
        while let Some(Q(d, c)) = pq.pop() {
            if c == goal { break; }
            if d > *dist.get(&c).unwrap_or(&f64::INFINITY) { continue; }
            for n in self.world.steps_from(c) {
                let step = match cost.get(&n) { Some(v) => *v, None => continue };
                let nd = d + step;
                if nd < *dist.get(&n).unwrap_or(&f64::INFINITY) {
                    dist.insert(n, nd);
                    prev.insert(n, c);
                    pq.push(Q(nd, n));
                }
            }
        }
        let mut path = Vec::new();
        let mut c = goal;
        while c != start {
            path.push(c);
            c = match prev.get(&c) { Some(p) => *p, None => return Vec::new() };
        }
        path.reverse();
        path
    }
}

fn world_band(world: &World, src: Cell, layer: Layer) -> HashMap<Cell, f64> {
    world.band_field(src, layer.decay(), &layer.transmission())
}

/// A leaderless man: the rising filter strips his song from the bottom, and
/// each time it eats his root the next note shifts into the root slot.
/// The same operation a messenger runs on arrival — the root slot is a
/// cursor, advanced by decay or by progress.
pub struct Wandering {
    pub notes: Vec<Note>,
    pub hpf: f64,
}

impl Wandering {
    pub fn new(mut notes: Vec<Note>) -> Wandering {
        notes.sort_by(|a, b| a.hz.total_cmp(&b.hz));
        Wandering { notes, hpf: HPF_START_HZ }
    }
    pub fn root(&self) -> Option<Note> {
        self.notes.first().copied()
    }
    /// Decay: the filter climbs and the current root falls away.
    pub fn tick_filter(&mut self) {
        self.hpf *= HPF_MULT_PER_TICK;
        self.notes.retain(|n| n.hz >= self.hpf);
    }
    /// Progress: a messenger reaching a checkpoint drops his current root and
    /// the next stop becomes it.
    pub fn arrive(&mut self) {
        if !self.notes.is_empty() {
            self.notes.remove(0);
        }
    }
}

/// A part of a company's score: a chord, how many voices it wants, and how
/// many are singing it. Addressed by type and count, never by identity.
pub struct Part {
    pub chord: Vec<Note>,
    pub wanted: i32,
    pub voiced: i32,
}

impl Part {
    pub fn missing(&self) -> i32 { (self.wanted - self.voiced).max(0) }
}

/// A stray is drawn to the company whose chord contains its root AND which
/// has a gap. Attraction is by harmonic complementarity, not amplitude: a
/// full chord cannot be improved, an incomplete one resolves.
pub fn attraction(stray_root: &Note, companies: &[Vec<Part>]) -> Option<usize> {
    let mut best: Option<(f64, usize)> = None;
    for (i, parts) in companies.iter().enumerate() {
        for p in parts {
            if p.chord.iter().any(|n| n.same(stray_root)) && p.missing() > 0 {
                let s = 1.0 + p.missing() as f64;
                if best.map_or(true, |(b, _)| s > b) {
                    best = Some((s, i));
                }
            }
        }
    }
    best.map(|(_, i)| i)
}
