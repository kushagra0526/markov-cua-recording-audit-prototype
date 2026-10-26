# cuaqa: coordinate-space and narration audit for computer-use recordings

Markov sells computer-use datasets: "screen recordings + synced mouse/keyboard events + narrations" with gold outputs and rubrics (https://www.markovstudios.com/). One failure that never shows in a schema check: the recorded click coordinates are in a different space from the screen they are labelled against (a 2x HiDPI capture, a second monitor with an origin offset), or the narration clock is shifted against the input clock. Every click then trains the model on the wrong UI element. This prototype audits one session for that, on synthetic data.

## What it does
Input: UI element boxes (as from an accessibility snapshot), click events (t, x, y), and narration lines (t, label). Output `ACCEPT` / `FIX` / `REJECT`:
- **Coordinate fit:** try 9 scales x 9 monitor offsets; the transform that puts the most clicks on an interactive element wins (canvas clicks are neutral, since a CAD viewport has no elements). Named `COORD_SCALE`, `COORD_OFFSET` or `COORD_SCALE_OFFSET`, with repaired targets for every click. If no known transform puts half the clicks on an element: `REJECT` with `COORD_UNFITTED`.
- **Narration clock:** shift in 0.25 s steps that makes narrated labels agree with clicked elements (`NARRATION_SHIFT`).
- **Label mismatch:** after the fit, a narration line that names a different element than the one clicked (`LABEL_MISMATCH`, with line index).

## Results (synthetic sessions, one planted defect each, about 1/3 clean)
Dev: seeds 0-299: 217/217 defective sessions stopped and named, 0/83 clean stopped; every click's target correct after repair (17,973/17,973, vs 10,380 as recorded). Schema check (increasing times, coordinates inside 1920x1080): 120/217 of the defective sessions.

Held-out: seeds 1000-1399 with scales (1.4, 0.8) and monitor offsets ((-1366,0), (2560,0)) that are not in the search grid, committed before the first run:

| Held-out, 400 sessions | schema check | cuaqa |
|---|---|---|
| defective sessions stopped (274) | 162 | 274 |
| clean sessions stopped (126) | 0 | 0 |
| named with the exact right code | - | 223 |
| `REJECT` (coordinate space not in the grid) | - | 25 |
| clicks whose target is right | 13,087 / 23,894 (as recorded) | 21,698 / 23,894 after repair |

Narration shift and label swap were 89/89 named and 45/45 flagged on the right line. The unseen coordinate spaces were all stopped but not all fixed: 25 sessions came back `COORD_UNFITTED` (their clicks count as wrong above because nothing is repaired), and the other 26 not named exactly were fitted to the nearest grid value (1.4 -> 1.33 or 1.5), which leaves part of their clicks on the wrong element.

## Read this before believing the table
The sessions, the defects and the checker are all mine, and the checker searches exactly the family of transforms the generator draws from, so dev is close to circular. The assumptions that matter: you have an element snapshot per session (a CAD or canvas-only app might not), the UI does not move mid-session (a moved window needs one snapshot per segment), narration leads the click by about 0.6 s, and labels are unique. Clicks inside a canvas cannot be checked at all. Nothing uses Markov data, datasets or systems.

## Run it (3 commands)
```
pip install pytest
python -m pytest -q tests
python -m cuaqa.run
```
Standard library only. 4 tests.

Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Markov.
