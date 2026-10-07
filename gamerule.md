# Sokobond express rule

* A level has 1 to 4 starts (each a player atom with its own molecule) and as
many exits. Each start draws its own path, which ends on any exit; each exit
takes exactly one path.
* A path starts on its player's atom and ends on an exit. It stays on level
tiles and can't pass through the same tile twice, and paths can't share tiles
with each other.
* A molecule slides one tile per path step. Atoms attached to it may hang
outside the level while moving, but must all be inside it at the end.
* A molecule atom may never move into a tile holding another atom or electrons.
* To win, every path must reach an exit, and every atom must belong to some
molecule, be neutral and use up all its free electrons.
* Each start has a leaving direction restricting its first move, and each exit
an entering direction restricting the final move into it. Since a start's first
move is forced, it is drawn automatically and not counted as a move.
* Cannot draw a path past any initial atoms, initial electrons, start point, end point.
* A start can be on the same tile as an exit, forming a loop: the path leaves
the start and ends when it comes back to it (entering from the exit's direction,
if it has one).
* A crossing is a tile paths may pass twice: once horizontally and once
vertically. On a crossing a path must go straight on, never turn 90 degrees.
Nothing starts on a crossing, and an exit is never one.

## Time

* Molecules on different paths move at the same time, one step per time step.
* After the moves, electron capture and bonding happen (in the same time step,
chain reactions included). A molecule that captured or bonded spends the next
time step reacting and does not move. This includes bonds and captures right at
the start of the level: they take the first time step. A molecule whose path
has reached its exit stops there and stays on the board.
* Molecules must never collide. Atoms can't move into anything standing still,
and two atoms can't end in the same cell. Between two moving molecules:
  1. moving in the same direction never collides;
  2. moving in opposite directions is checked as if movement were continuous,
  so they can't swap places;
  3. moving perpendicular only compares the cells before and after the move, so
  an atom may move into a cell another molecule is leaving sideways. For
  example, N-N moving up while O=O (vertical, to its right) moves left into the
  cell the N just left is fine.

## Bonding

After each step, electron capture happens first, then bonding. Bonding can use
free electrons that were just captured.

* A free atom is an atom with free electrons.
* Two free atoms can bond when they are adjacent and either one is in a
molecule and the other is loose (as they were when the current phase began, see
below), or both are in the same molecule (for example closing a ring). Loose
atoms never bond with each other.
* Molecules never merge: atoms of two molecules never bond, and an atom can't
bond to two molecules. A loose atom whose possible partners belong to two
molecules is ambiguous.
* Bonds that existed before bonding started this step never change multiplicity,
and those neighbours don't count as possible partners.
* Ambiguity: a free atom with more possible partners than free electrons is
ambiguous. Any free atom that can bond with an ambiguous atom is also ambiguous
(this spreads). Ambiguous atoms don't bond.
* Every unambiguous atom forms one bond with each of its possible partners, all
at the same time. Loose atoms that bond join that molecule.
* This repeats in rounds until no bond forms, adding a second, third or fourth
bond to pairs bonded earlier in the same step (double/triple/quadruple bonds).
That is one phase.
* Loose atoms that bonded during a phase join the molecule only once the phase
is over; then a new phase lets them bond with further loose atoms (chain
reaction). Phases repeat until no molecule grows. For example, with H-c next to
loose O-H, the C and O form a double bond first, which leaves the O no free
electrons, so the last H stays loose.

## Ions and electrons

* A positive ion is an atom with less free electrons than normal: each charge
is one less free electron. An ion is not neutral until its charge is gone.
* Electrons sit on cells; several can share one cell. When a molecule ion ends
a step next to a cell holding electrons, it captures one electron from that
cell (one per cell it touches), losing one charge and gaining one free electron.
Only molecules that moved in that time step capture (capturing is a touch).
Capture has its own ambiguity check, worked out like bonding's but separately
from it: a cell touching more molecule ions than it holds electrons is
ambiguous, and so is an ion touching more electron cells than its charge.
Anything that could capture from, or be captured by, an ambiguous ion or cell is
ambiguous too (this spreads). The other ions each capture one electron from
every cell they touch, all at the same time.
* Some atoms and electrons start on holes instead of level tiles.

## Rotators

* A rotator sits on a grid corner (where four cells meet), drawn as an asterisk.
Since molecules can go off the grid, rotators can also sit on the grid's
boundary corners.
* As a molecule moves, each bond that lies across the direction its nearer atom
moves (nearer to the player along the molecule) sweeps over the grid corner
beside it. If that corner has a rotator, the bond is turned around it: the
farther atom, and everything attached through it, moves into the nearer atom's
old cell instead of following. Directions are worked out outward from the
player, nearest bond first, each using the direction its nearer atom just got,
so one rotator can turn several bonds in one move.
* Example (player p, rotator * between 2, p, 5 and 6), moving down:

      From:          To:
        1              1
        |              |
        2-p-3      4-5-2
        |*           |*|
      4-5-6          6 p-3
          |          |
          7          7

  p and 3 move down, 1 and 2 move right, 4 and 5 move up, 6 and 7 move left.
* Turning happens during the move and takes no extra time; capture and bonding
happen afterwards as usual.
