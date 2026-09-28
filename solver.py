#!/usr/bin/env python3
"""Sokobond Express solver.

Finds the shortest path to draw from the starting atom to the exit.

Rules modelled:
  * The drawn path starts on the player's atom and ends on the exit. It stays
    on level tiles and can't pass through the same tile twice.
  * The molecule slides one tile per path step. Atoms attached to it may hang
    outside the level while moving, but must all be inside it at the end.
  * Any molecule atom with a free electron that ends a step next to another
    atom with a free electron bonds with it (one bond), pulling it (and
    whatever it's bonded to) into the molecule.
  * A molecule atom may never move into a tile holding another atom.
  * To win, the molecule must have no free electrons left.

Level format (plain text grid):
    .           level tile
    E           exit tile
    # or space  outside the level (atoms may pass over it, the path may not)
    H O N C     loose atoms with 1, 2, 3, 4 electrons
    h o n c     the player's starting atom
    Other letters: give them a valence with --valence X=N.

Example:
    ..H..
    o...E
    ..H..
"""
import argparse
import sys
from collections import deque

DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
VALENCE = {"H": 1, "O": 2, "N": 3, "C": 4}


class Level:
    def __init__(self, text, valence):
        rows = [r.rstrip("\n") for r in text.splitlines()]
        while rows and not rows[-1].strip():
            rows.pop()
        while rows and not rows[0].strip():
            rows.pop(0)
        self.h, self.w = len(rows), max(len(r) for r in rows)
        self.tiles, self.exit = set(), None
        elems, positions, player = [], [], None
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch in "# ":
                    continue
                self.tiles.add((r, c))
                if ch == "E":
                    self.exit = (r, c)
                elif ch.upper() in valence:
                    if ch.islower():
                        if player is not None:
                            sys.exit("Only one player atom (lowercase letter) allowed")
                        player = len(elems)
                    elems.append(ch.upper())
                    positions.append((r, c))
                elif ch != ".":
                    sys.exit(f"Unknown tile {ch!r} at row {r + 1}, col {c + 1}")
        if player is None:
            sys.exit("No player atom (lowercase letter) found")
        if self.exit is None:
            sys.exit("No exit tile E found")
        # Keep the player atom at index 0.
        order = [player] + [i for i in range(len(elems)) if i != player]
        self.elems = tuple(elems[i] for i in order)
        self.valence = tuple(valence[e] for e in self.elems)
        self.bit = {p: 1 << k for k, p in enumerate(sorted(self.tiles))}
        pos = tuple(positions[i] for i in order)
        self.start = bond(self, pos, frozenset([0]), frozenset(), tuple(self.valence))


class State:
    """Atom positions, the player's molecule, its bonds and free electrons.

    Bonds are only kept for display: the future depends on positions, which
    atoms are in the molecule and how many free electrons each atom has.
    """
    __slots__ = ("pos", "mol", "bonds", "free", "_key", "_hash")

    def __init__(self, pos, mol, bonds, free):
        self.pos, self.mol, self.bonds, self.free = pos, mol, bonds, free
        self._key = (pos, mol, free)
        self._hash = hash(self._key)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return self._key == other._key

    def need(self):
        """Free electrons left on the molecule."""
        return sum(self.free[i] for i in self.mol)


def bond(level, pos, mol, bonds, free):
    """Bond the molecule to adjacent atoms until nothing more can bond."""
    if not any(free[i] for i in mol):
        return State(pos, mol, bonds, free)
    mol, bonds, free = set(mol), set(bonds), list(free)
    at = {p: i for i, p in enumerate(pos)}
    changed = True
    while changed:
        changed = False
        # Deterministic order: molecule atoms by position, neighbours U/D/L/R.
        for i in sorted(mol, key=lambda i: pos[i]):
            r, c = pos[i]
            for dr, dc in DIRS.values():
                if not free[i]:
                    break
                j = at.get((r + dr, c + dc))
                if j is None or j in mol or not free[j]:
                    continue
                bonds.add((min(i, j), max(i, j)))
                free[i] -= 1
                free[j] -= 1
                mol.add(j)
                changed = True
    return State(pos, frozenset(mol), frozenset(bonds), tuple(free))


def step(level, state, d):
    """Slide the molecule one tile. Returns the new state, or None on collision."""
    dr, dc = DIRS[d]
    mol = state.mol
    pos = list(state.pos)
    occupied = {p for i, p in enumerate(pos) if i not in mol}
    for i in mol:
        r, c = pos[i]
        pos[i] = p = (r + dr, c + dc)
        if p in occupied:
            return None
    return bond(level, tuple(pos), mol, state.bonds, state.free)


def is_win(level, state, all_atoms):
    if state.pos[0] != level.exit or state.need():
        return False
    if any(state.pos[i] not in level.tiles for i in state.mol):
        return False
    return not all_atoms or len(state.mol) == len(state.pos)


def can_finish(level, state):
    """The molecule can only fill its free electrons from atoms outside it."""
    if not state.need():
        return True
    return any(f for i, f in enumerate(state.free) if i not in state.mol)


def exit_reachable(level, lead, visited):
    """Can the path still reach the exit through unused tiles?"""
    bit = level.bit
    seen, stack = visited | bit[lead], [lead]
    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS.values():
            p = (r + dr, c + dc)
            if p == level.exit:
                return True
            b = bit.get(p)
            if b and not seen & b:
                seen |= b
                stack.append(p)
    return False


def finish(level, state, visited):
    """Shortest route to the exit for a molecule that can no longer bond.

    Its shape is fixed from here on, so the lead tile is the whole state and a
    plain BFS gives the shortest path (which never repeats a tile anyway).
    """
    lr, lc = state.pos[0]
    shape = [(state.pos[i][0] - lr, state.pos[i][1] - lc) for i in state.mol]
    blocked = {p for i, p in enumerate(state.pos) if i not in state.mol}

    def fits(r, c):
        return all((r + dr, c + dc) not in blocked for dr, dc in shape)

    def inside(r, c):
        return all((r + dr, c + dc) in level.tiles for dr, dc in shape)

    prev = {(lr, lc): None}
    queue = deque([(lr, lc)])
    while queue:
        r, c = queue.popleft()
        if (r, c) == level.exit:
            if not inside(r, c):
                return None  # only one way to arrive matters: the exit ends the path
            path = []
            while prev[r, c]:
                (r, c), d = prev[r, c]
                path.append(d)
            return "".join(reversed(path))
        for d, (dr, dc) in DIRS.items():
            p = (r + dr, c + dc)
            b = level.bit.get(p)
            if b and not visited & b and p not in prev and fits(*p):
                prev[p] = ((r, c), d)
                queue.append(p)
    return None


def solve(level, all_atoms=False, max_len=0):
    """Breadth-first search over (board state, tiles the path has used)."""
    start = level.start
    visited0 = level.bit[start.pos[0]]
    # For each board state, the used-tile sets it has been reached with. A new
    # arrival whose used tiles are a superset of an earlier one can't do better.
    seen = {start: [visited0]}
    queue = deque([(start, visited0, "")])
    best = None
    while queue:
        state, visited, path = queue.popleft()
        if best is not None and len(path) >= len(best):
            break
        if not state.need():
            if all_atoms and len(state.mol) != len(state.pos):
                continue
            rest = finish(level, state, visited)
            if rest is not None and (best is None or len(path) + len(rest) < len(best)):
                best = path + rest
            continue
        # The path ends on the exit, so it can't continue past it.
        if state.pos[0] == level.exit or (max_len and len(path) >= max_len):
            continue
        r, c = state.pos[0]
        for d, (dr, dc) in DIRS.items():
            lead = (r + dr, c + dc)
            b = level.bit.get(lead)
            if not b or visited & b:
                continue
            nxt = step(level, state, d)
            if nxt is None or not can_finish(level, nxt):
                continue
            nv = visited | b
            if lead != level.exit and not exit_reachable(level, lead, nv):
                continue
            masks = seen.setdefault(nxt, [])
            if any(m & nv == m for m in masks):
                continue
            masks.append(nv)
            queue.append((nxt, nv, path + d))
    if best is not None and max_len and len(best) > max_len:
        return None
    return best


def render(level, state, trail=()):
    cells = set(level.tiles) | set(state.pos)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    c1 = max(c for _, c in cells)
    grid = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r, c] = "." if (r, c) in level.tiles else " "
    grid[level.exit] = "E"
    for p in trail:
        if grid[p] == ".":
            grid[p] = "*"
    for i, p in enumerate(state.pos):
        e = level.elems[i]
        grid[p] = e.lower() if i in state.mol else e
    return "\n".join("".join(grid[r, c] for c in range(c0, c1 + 1)).rstrip()
                     for r in range(r0, r1 + 1))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("level", help="level file ('-' for stdin)")
    ap.add_argument("--all-atoms", action="store_true",
                    help="also require every atom on the board to join the molecule")
    ap.add_argument("--valence", action="append", default=[], metavar="X=N",
                    help="add or override an element's electron count")
    ap.add_argument("--max-len", type=int, default=0, help="limit path length")
    ap.add_argument("--quiet", action="store_true", help="don't print each step")
    args = ap.parse_args()

    valence = dict(VALENCE)
    for v in args.valence:
        e, n = v.split("=")
        valence[e.upper()] = int(n)
    text = sys.stdin.read() if args.level == "-" else open(args.level).read()
    level = Level(text, valence)

    path = solve(level, args.all_atoms, args.max_len)
    if path is None:
        print("No solution found.")
        sys.exit(1)
    print(f"Solution ({len(path)} moves): {path}")
    if not args.quiet:
        state, trail = level.start, [level.start.pos[0]]
        print("\nStart:\n" + render(level, state, trail))
        for i, d in enumerate(path, 1):
            state = step(level, state, d)
            trail.append(state.pos[0])
            print(f"\n{i}. {d}\n" + render(level, state, trail))


if __name__ == "__main__":
    main()
