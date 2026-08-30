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

/// Constants of the behavioural substrate. Same warning as the rest of this
/// file: the orderings are Will's, the numbers are provisional.
pub mod soma {
    /// Seconds a tick represents.
    pub const TICK_SECONDS: f64 = 0.1;

    /// Arousal at which the border is half open.
    pub const AROUSAL_SCALE: f64 = 2.0;
    /// Half-life of a fresh spike, seconds.
    pub const TAU_AROUSAL: f64 = 4.0;
    /// How much load stretches that half-life. Shaking hands are a longer
    /// time constant, not a stat.
    pub const BETA: f64 = 3.0;
    /// How much load sharpens the response to an event. The battered man
    /// jumps at timber creaks because his threshold collapsed.
    pub const KAPPA: f64 = 1.5;
    /// How much load stiffens the border. Load builds the fence; arousal
    /// dissolves it. The veteran will not leave his mates.
    pub const FENCE_LOAD: f64 = 1.0;

    /// Fast into slow.
    pub const ALPHA: f64 = 0.1;
    /// Where the latch trips.
    pub const LOAD_MAX: f64 = 10.0;
    /// Fraction of the ceiling load must fall back below before the latch
    /// clears. With no bath it never falls, so the rule rarely fires — the
    /// physics does the work and this is only the guard.
    pub const NUMB_CLEAR: f64 = 0.6;

    /// Drain time at the reference choir, seconds.
    pub const TAU_CHOIR: f64 = 90.0;
    /// The choir size that drain time refers to.
    pub const CHOIR_REF: f64 = 8.0;
    /// Below this the bath is simulated mode by mode and rings.
    pub const BATH_CAP: usize = 4;
    /// Centre of the ally mode band, radians per second.
    pub const BATH_OMEGA: f64 = 0.15;
    /// Half-width of the band in log space.
    pub const BATH_LAMBDA: f64 = 0.6;
    /// How hard load couples into the bath.
    pub const BATH_COUPLING: f64 = 0.30;

    /// The constant in the fix-strain law, fitted against exact curvature
    /// across both degenerate strata (2.25x residual, inside the character
    /// variance the exact constant carries anyway).
    pub const STRAIN_K: f64 = 8.0;
    /// Strain in open, well-spread geometry. Only the excess is suspense.
    pub const STRAIN_REST: f64 = 1.0;
    /// How hard bad geometry drives arousal, at the limit. Quiet is
    /// dangerous, but a man's dread is bounded even when his fix is not.
    pub const SUSPENSE_GAIN: f64 = 0.35;
    /// Half-point of the dread curve, in log-strain. Strain diverges at a
    /// degenerate frame; suspense is read off its logarithm, which is the
    /// scale everything else acoustic is already on.
    pub const STRAIN_HALF: f64 = 8.0;
    /// Floor on the determinant so a perfectly degenerate frame is merely
    /// very bad rather than infinite.
    pub const DEGENERACY_FLOOR: f64 = 1e-6;

    /// Amplitude at which a band counts half toward fidelity. Hearing a
    /// note at all is most of the value; hearing it loudly adds little.
    pub const FIDELITY_HALF: f64 = 0.5;
    /// How much arousal costs a man of the song. The somatic layer taking
    /// gain is the same event as the subconscious losing it — this is the
    /// coupling that closes the panic loop.
    pub const ATTENTION_COST: f64 = 0.6;
    /// Fidelity a man would have with a perfect chord and a clear head. He
    /// never quite gets there, which is why the anchor is never exactly
    /// orthogonal to the world.
    pub const FIDELITY_CEIL: f64 = 0.97;
}
