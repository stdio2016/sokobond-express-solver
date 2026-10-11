# Sokobond Express solver — handoff

A browser solver, level editor and player for **Sokobond Express** puzzles.
Everything lives in one self-contained page, `web/index.html` (no build step,
no dependencies beyond Google Fonts). Open it directly in a browser, or use
the published artifact.

- **Live page:** https://claude.ai/artifact/Q5JArE2514RUWMDCxqH4wi
  (shared with anyone who has the link). Republish with the Artifact tool: in the session
  that published it, use the same `file_path`. From a new session, pass that
  URL as `url` after an `action: "read"`. Publishing without `url` creates a
  new artifact.
- **Game rules:** `gamerule.md` is the source of truth. Keep it in sync with
  the engine whenever a rule changes.
- **Remote:** github.com/stdio2016/sokobond-express-solver. Branch `master`;
  nothing has been pushed by Claude so far.

## Working agreements (from the owner)

- **Game rules are hard-coded, never UI options,** unless the owner explicitly
  asks for a toggle. Search limits (max time steps, state limit) are fine as
  inputs.
- **Don't save levels the owner pastes from the game anywhere** (repo, page,
  samples, scratch files, browser localStorage). They may be copyrighted. Test
  them in memory only (see Testing). `levels/official/` already holds a few
  levels the owner committed; don't add to it without asking.
- **Commit only when asked,** with a descriptive message. Never commit
  `.DS_Store`, `.claude/settings.local.json` or untracked files you didn't
  create.
- When a rule is ambiguous, ask with concrete options. The owner is
  reverse-engineering the real game and answers precisely.
- **Copy style for the page:** plain, active voice, specific error messages
  that say how to fix the problem.
- Computer use can't open the game itself: "SokobondExpress" is blocked by
  policy for computer use. The owner tests solutions in the game and reports
  back, often as an arrow string like `→↑←↓…`.

## Architecture (`web/index.html`)

| Section | Rough lines | What it is |
|---|---|---|
| CSS | 1–180 | Theme tokens (light and dark), `--p0..--p3` path colours, `--electron`, `--used` (grey ghosts). Mode visibility: `body[data-mode]` with `.edit-only/.solve-only/.try-only`. `[hidden]{display:none!important}` is required for self-hosting. |
| HTML | 180–300 | Header with the Edit/Solve/Try switch; board (`.board-wrap` is a square made with `padding-bottom:100%`, not `aspect-ratio`, for Safari; the SVG is positioned absolutely inside it); try panel; sidebar with the solution steps (`#result-panel`), Level panel and Solve panel. |
| `<script id="engine-src">` | ~302–800 | **Engine and solver.** Runs on the page (try mode, playback) and as the solver's Web Worker (built from this script's text through a Blob). Wrapped in `const Engine = (() => {…})()`; exports `OFF, DK, makeEngine, solve, solveSplit`. |
| Main script | ~800–end | Level text ↔ model, drawing, editor, solve UI, try mode, wiring. |

### Engine (`makeEngine(L)`)

`L` comes from `buildLevel()` and contains: `tiles, exits, exitDirs,
crossings, rotators` (cell codes), `electrons [{p,n}]`, `players` (P),
`startDirs`, atom arrays `pos, elems, valence, charge` (atoms `0..P-1` are the
starts, in reading order), and `maxLen, limit`.

- **Cell code:** `(r+512)*1024 + (c+512)`. `OFF = {U:-1024, D:1024, L:-1, R:1}`.
  A rotator corner r,c uses the same code as cell r,c (its top-left corner).
- **State:** `{pos, mid, bonds, free, charge, elec, paused, done, key}`.
  - `mid[i]` is the atom's molecule id, or -1 if loose.
  - `paused` and `done` are bitmasks over molecules.
  - `key` covers everything that affects the future, including the set of
    bonded pairs.
- `react()` runs capture (with its own ambiguity check, only for molecules
  that moved), then bonding in phases of rounds (ambiguity spreads, molecules
  never merge, chain reactions happen in later phases). It returns which
  molecules reacted.
- `atomDirs()` works out each atom's direction for the step, spreading
  rotator turns outward from the player along bonds.
- `step(s, dirs)` moves molecules one time step and checks collisions:
  - nothing moves into standing atoms or electrons;
  - no two atoms end in the same cell;
  - same direction never collides;
  - opposite directions can't swap;
  - perpendicular moves only compare cells before and after.

  After moving it calls `react()`. Molecules that reacted pause for the next
  step (multi-start levels only).
- `simulate(paths)` replays full paths (forced first steps included) and
  returns frames, `tip` (when each path ends), `moveTicks` and the collision
  step. Try mode and the solution playback both use it.
- `canFinish(s)` is the dead-end check. `isWin(s)` requires all paths done,
  every atom in a molecule and settled, and every molecule inside the level.

### Solver (`solve(L)`)

- **Search:** breadth-first over time steps, choosing a move for every moving
  molecule at each step (paths never wait; forced first steps are taken).
  The first win found has the fewest time steps; with one start, that's the
  fewest moves.
- **Used tiles:** `Int32Array` words, not BigInt. BigInt was very slow,
  especially in Safari. A crossing has a second bit for its vertical pass.
- **Dominance:** for each state `key`, the solver keeps the *free regions*
  it has been reached with (unused tiles reachable from the moving leads; see
  `freeRegion`). A new arrival is dropped if its region fits inside an earlier
  one. Entries made redundant by a newer, larger region are removed. This cut
  Zeta-4 from 1.14M states and 61s (Safari) to 58k states and about 0.25s.
- **Pruning to keep valid:** whenever a mechanic can change a molecule's
  shape or timing, re-check every prune.
  - `finish()` shortcut: only one start, no crossings, no rotators. It
    assumes a fixed shape and that nothing else moves.
  - Dropping arrivals at the exit unsettled: one start only.
  - `canFinish`: a ring can still close if an internal pair is pending, or if
    rotators exist and the molecule has ≥2 atoms with free electrons or
    charge. Rotators broke the old assumption: Xi-6 was missed until this was
    fixed.
- **Output:** `paths` (without forced first steps), `full`, `moves`, `ticks`,
  `moveTicks`, `frames`.

### Split solver (`solveSplit(L, opt)`), for several starts

The joint search above grows as the product of every start's choices, so
late multi-start levels ran out of memory. The worker runs `solve()` for up
to 5 s / 300k states first (it proves the fastest answer on easy levels),
then `solveSplit()` within the page's "Time limit" input (default 180 s). Its answers are
valid (they replay to a win) but **not proven fastest**; the page says so.

- **Worlds:** each start is planned alone (`plan()`, an A* over time steps)
  in a world with only its own atom, the loose atoms it may take
  (`spec.forbid` hides atoms), its share of electrons (`spec.caps`), and
  pausing as in the full level (`L.pause`). Tiles where anything starts are
  blocked (`L.blocked`), and so are other starts' forced first-step tiles.
- **Search:** conflict-based. The plans are checked together (`conflict()`):
  an atom taken twice or by nobody, an atom still in one world that another
  plan takes, too many electrons from one cell, a shared exit or tile, then a
  replay of the full level compared with each plan (collisions, or a molecule
  touching an atom another one takes). Each clash branches into constraints
  (forbid/require an atom, cap electrons, ban a tile or exit, or a timed
  constraint: V cell, E move, A adjacency, C collected by, X electrons gone
  by) and the affected start is re-planned.
- **`respond()`:** on every clash it also re-plans one of the starts against
  the others' current paths in the full level (exact replay). This catches
  what separate worlds can't, like making a bond ambiguous on purpose
  (Omega-o6) or one loop going around another (Omega-h6). Its wins enter the
  queue as finished nodes.
- **Starting points:** when there are at most 64 ways to share the loose
  atoms out between the starts (each share must be able to complete its
  molecule, `completes`), each share is its own starting point with every
  atom owned, so no world holds atoms it won't take, plus an "open" one
  where any start may take any atom and ownership is settled clash by clash
  (it often finds a first answer fastest, so it gets a head start and stops
  taking turns after 100k states without an answer). With more shares
  (Omega-99) only the open one.
- **Order:** each starting point has three queues over its nodes, popped in
  turn: fewest time steps; fewest clashes plus tile bans; and a dive (newest
  clash's first branch). Each pop goes to the starting point that has used
  the least work. Child plans start on a 30k-state budget; one that runs out
  waits in the queue and retries with 4× the budget (weighted A* only).
  Once a solution is known, plans slower than it are cut (`capTicks`). It
  returns the best found when the queues empty or the time runs out, and
  reports each improvement (`onBest`) so Stop keeps it.
- **Planner pruning:** `completable`/`completes` (can the atoms left still
  complete the molecule by valence counting), and the A* bound in `heur`:
  the lead's distance to an exit, and for each set of atoms and electron
  cells that could finish the molecule, the farthest one, the trip between
  any two (less the molecule's length), and from each to an exit. Plans that
  run out of states retry with a weighted bound (`opt.tries`).
- **Debugging:** `opt.debug` receives the internals (`plan`, `respond`,
  `conflict`, `world`, `stats`); `opt.noSearch` stops before searching;
  `opt.log`/`opt.planLog` trace nodes and plans.

### Level text format

Rows of cells:
- `.` tile, `#`/space hole, `E` exit, `+` crossing, `-` electron;
- `HONC` loose atoms, lowercase letters for starts;
- bracket groups for anything more:
  - `[O+]` ion (one `+` per charge);
  - `[--]` several electrons;
  - `[H#]` on a hole;
  - `[oE]` start on an exit (a loop);
  - `[o>]` start direction, `[E^]` exit direction (`^ v < >`).

Directive lines: `start=R`, `exit=D` (defaults for every start and exit),
`valence: X=2`, `rotators: r,c r,c`. Levels with one start and one exit
serialize with `start=`/`exit=` lines, so older texts round-trip unchanged.

## Testing

There's no test suite. Test in the **built-in browser pane**:
1. `navigate` to `file:///Users/chenyifeng/Documents/sokobond%20express%20solver/web/index.html`.
2. Wait about 300 ms; running JS too early reports `parseLevel is not defined`.
3. Run JS:

```js
self.postMessage = () => {};                 // solve() posts progress
M = parseLevel(text); const L = buildLevel(); // don't call loadText for private levels (it saves to localStorage)
const r = Engine.solve(L);                    // {type, paths, moves, ticks, full, nodes}
const G = Engine.makeEngine(L); const sim = G.simulate(r.full);
G.isWin(sim.frames.at(-1));                   // a solver answer must replay to a win
```

- **Regression check:** solve every entry of `SAMPLES` and compare with the
  paths below. Any change means behaviour changed.
  - Water `RRR`
  - Two corners `RDDRRRU`
  - Ammonia `DRUURRURRDDDDRR`
  - Small starter `URRRDR`
  - Oxygen ion `DDRRRRRR`
  - Hydrogen over a hole `RRDRR`
  - Electron over a hole `RDRRRUURRRDR`
  - Double charge `URDDRURRRR`
  - Crossing `RRRRUULLDDDD`
  - Loop `ULDDRRUL`
  - Rotator `RDDRRR`
- **Several starts:** `Engine.solveSplit(L, { timeLimit: ms })` returns the
  same shape (plus `split: true`, `nodes` = branches). Browser tool calls
  time out after about a minute, so run long searches in a Worker built from
  `$("engine-src").textContent` and poll for the result. Opening a new tab
  in the pane can reload the page and orphan running workers.
- **Missed-solution reports:** replay the owner's path with `G.step` one step
  at a time to find where it's refused. If the rules accept the path, test
  each prune (`canFinish`, `freeRegion`) along it to find the one cutting it
  off.
- **Hand-built states** for rule cases: `G.step({pos, mid, bonds, free,
  charge, elec, paused: 0, done: 0}, dirs)` (see the rotator example in
  `gamerule.md`).
- Safari behaves differently (layout, BigInt speed, touch). The owner tests
  on Safari, so mention when a change couldn't be verified there.

## Open questions and assumptions to confirm with the owner

- **Paths:** they can't share tiles (a crossing allows one pass each way, by
  any paths). With several starts, "best" means fewest time steps.
- **Timing:** reactions are worked out right after the moves. Only molecules
  that moved capture electrons.
- **Ions:** an ion touching more electron cells than its charge is ambiguous
  (mirrors bonding). Only molecule ions capture; loose ions never do.
- **Rotators in rings:** can't happen in the real game, so the owner chose
  Sokobond's behaviour: if two bond routes disagree the bond would tear and
  the move is refused ("torn"); a 4-ring around a rotator turns as a whole
  (see `gamerule.md`).
- **Untested:** 3- or 4-start levels. The split solver hasn't solved
  Omega-99 (4 starts, ten H) yet. Omega-n5 takes about a minute (Node): its
  plans wall in each other's forced first steps, which is only learned a
  tile ban at a time, and one O²⁺ plan needs ~170k states. A* dominance lists
  get long there (the check dominates plan time); capping them was tried and
  made n5 worse.

## Ideas for next steps

- **Solver speed:**
  - The state `key` is a long string built on every step. A compact hash or
    typed-array key would help.
  - `react()` allocates Maps and Sets on every step.
  - Split solver: with more than 64 shares only the open starting point
    runs, and branching on ownership one atom at a time is slow with many
    atoms (Omega-99 has ten H). Sharing by groups of atoms might help.
  - States hold full arrays and a key string; memory limits the plan and
    respond searches more than time does.
- **UI:**
  - A time-step slider in Try mode.
  - A clearer selected-path highlight.
  - A rotator preview when hovering a move.
  - Show why the solver found nothing (which prune ended each branch).
- **Levels:** importing the owner's level files with "Open file…" already
  works; batch-solving a folder would help regression testing (keep private
  levels local).
