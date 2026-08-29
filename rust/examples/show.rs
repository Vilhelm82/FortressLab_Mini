use fortress_sim::devmap;
use std::collections::HashMap;

fn main() {
    let w = devmap::build();
    let mut m = HashMap::new();
    m.insert((16, 4, 1), 'M');
    println!("{}", w.section(4, 5, &m));
    println!("\n  a man at x=16 on the ground can reach:");
    let mut seen = vec![(16, 4, 1)];
    let mut frontier = vec![(16, 4, 1)];
    while let Some(c) = frontier.pop() {
        for n in w.steps_from(c) {
            if !seen.contains(&n) { seen.push(n); frontier.push(n); }
        }
    }
    let walk: Vec<_> = seen.iter().filter(|c| c.2 >= 3).collect();
    println!("  cells at wall-walk height or above: {}", walk.len());
    println!("  on the west curtain (x=12): {}",
        walk.iter().filter(|c| c.0 == 12).count());
    println!("  on the east curtain (x=33): {}",
        walk.iter().filter(|c| c.0 == 33).count());
    println!("  in a tower (h=3): {}",
        walk.iter().filter(|c| c.2 == 4).count());
}
