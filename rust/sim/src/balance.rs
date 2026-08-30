//! Balance constants.
//!
//! All provisional. Every value here expresses an ordering Will ruled —
//! depth is authority, highs die faster, stone kills detail — but the
//! numbers themselves are Claude's and are the R&D sweep's to overwrite.
//! The tests pin structure, never values.

use crate::world::Material;
use std::collections::HashMap;

/// Which octave a note sits in. Depth is authority: lower is stronger and
/// carries further.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum Layer {
    /// The location root — the region. Lowest, strongest, penetrates stone.
    Loc,
    /// The company leader — sergeant or knight.
    Lead,
    /// The dyad specifier — the sub-location. Blocked by stone.
    Spec,
    /// Extensions — conditions and tactics.
    Ext,
}

impl Layer {
    pub const ALL: [Layer; 4] = [Layer::Loc, Layer::Lead, Layer::Spec, Layer::Ext];

    /// Octave multiplier above the base pitch.
    pub fn octave(self) -> f64 {
        match self {
            Layer::Loc => 1.0,
            Layer::Lead => 2.0,
            Layer::Spec => 4.0,
            Layer::Ext => 8.0,
        }
    }

    /// How hard this band pulls. Depth is authority.
    pub fn weight(self) -> f64 {
        match self {
            Layer::Loc => 3.0,
            Layer::Lead => 2.0,
            Layer::Spec => 1.2,
            Layer::Ext => 1.0,
        }
    }

    /// Per-step survival. Highs die faster, which is the distance low-pass.
    pub fn decay(self) -> f64 {
        match self {
            Layer::Loc => 0.97,
            Layer::Lead => 0.94,
            Layer::Spec => 0.88,
            Layer::Ext => 0.80,
        }
    }

    /// What survives crossing a material. Stone kills detail and lets the
    /// bass through; timber leaks everything a little.
    pub fn transmission(self) -> HashMap<Material, f64> {
        let (stone, timber) = match self {
            Layer::Loc => (0.6, 0.9),
            Layer::Lead => (0.0, 0.6),
            Layer::Spec => (0.0, 0.5),
            Layer::Ext => (0.0, 0.4),
        };
        HashMap::from([
            (Material::Earth, 0.0),
            (Material::Stone, stone),
            (Material::Timber, timber),
            (Material::Stair, stone),
        ])
    }
}

/// Base pitch of the lowest octave. Arbitrary — one just has to be picked.
pub const BASE_HZ: f64 = 32.70;

/// Weakest usable echolocation return.
pub const ECHO_FLOOR: f64 = 1e-4;
/// A voice is audible only if it beats this fraction of the rest of the din.
pub const MASK_RATIO: f64 = 0.25;
/// Absolute audibility floor in silence.
pub const HEAR_FLOOR: f64 = 1e-5;
/// How far the perception beam reaches, in cells.
pub const BEAM_RANGE: f64 = 10.0;
/// Half-width of the perception cone, radians (~30 degrees).
pub const BEAM_HALFANGLE: f64 = 0.5236;
/// Weight of being observed in least-detection routing.
pub const LAMBDA_OBS: f64 = 0.3;
/// The inversion cascade sweeps from the bottom, geometrically.
pub const HPF_START_HZ: f64 = BASE_HZ;
pub const HPF_MULT_PER_TICK: f64 = 1.06;
