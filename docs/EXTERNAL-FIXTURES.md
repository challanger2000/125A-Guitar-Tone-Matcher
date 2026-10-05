# External high-gain validation fixtures

External audio is never committed to this public repository by default.

## Cambridge MT candidates

### Hollow Ground — Ill Fate
- Style: Death Metal
- Source: Cambridge MT Free Multitrack Download Library
- Useful because: isolated multitrack guitars, aggressive high-gain rhythm material
- Intended use: validation fixture only
- Status: source identified; automated direct download blocked by server policy

### Hollow Ground — Left Blind
- Style: Hardcore / high-gain rhythm guitar
- Source: Cambridge MT Free Multitrack Download Library
- Useful because: different production/tone from Ill Fate
- Intended use: validation fixture only
- Status: source identified

### Dark Ride — Deny Control
- Style: modern metal
- Source: Cambridge MT Free Multitrack Download Library
- Band notes explicitly ask mixers to preserve the intended guitar tone and cite a Killswitch Engage-era direction.
- Tempo: 124 BPM
- Useful because: modern tight rhythm guitars and a published reference mix/stems
- Intended use: validation fixture only
- Status: source identified; automated direct download blocked by server policy

## Telefunken Live From The Lab candidates

### Renesans — Season 9
- Source: TELEFUNKEN Live From The Lab
- Available sources include guitar DI and guitar amp tracks.
- Especially useful as a second paired DI/amp oracle with a completely different recording chain.
- License boundary: educational / demonstrational / non-commercial only.
- Intended use: internal validation only; never distributed with the product.

## Rules

1. Keep fixture audio outside git.
2. Record source URL, license/usage restriction, sample rate, channel layout and exact file identity.
3. Never train or ship a commercial model on material unless the license explicitly allows that use.
4. Validation-only material may be measured locally but must not be redistributed.
