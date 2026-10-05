# Sokobond express rule

* The drawn path starts on the player's atom and ends on the exit. It stays
on level tiles and can't pass through the same tile twice.
* The molecule slides one tile per path step. Atoms attached to it may hang
outside the level while moving, but must all be inside it at the end.
* A molecule atom may never move into a tile holding another atom or electrons.
* To win, every atom must be neutral and use up all its free electrons.
* Start point has a leaving direction restricting the first move, and end point also has a entering direction restricting the final move.
Since the first move is forced, it is taken automatically: the tile it leads to
becomes part of the path (an obstacle like the start) and drawing begins there.
It is not counted as a move.
* Cannot draw path past any initial atoms, initial electrons, start point, end point.
* The start point can be the same tile as the end point, forming a loop: the
path leaves the start and ends when it comes back to it (entering from the
exit's direction, if it has one).
* A crossing is a tile the path may pass twice: once horizontally and once
vertically. On a crossing the path must go straight on, never turn 90 degrees.
Nothing starts on a crossing, and the exit is never one.

## Bonding

After each step, electron capture happens first, then bonding. Bonding can use
free electrons that were just captured.

* A free atom is an atom with free electrons.
* Two free atoms can bond when they are adjacent and at least one of them is in
the molecule (as it was when the current phase began, see below). Loose atoms
only bond with the molecule, never with each other. Two molecule atoms can bond
too (for example closing a ring).
* Bonds that existed before bonding started this step never change multiplicity,
and those neighbours don't count as possible partners.
* Ambiguity: a free atom with more possible partners than free electrons is
ambiguous. Any free atom that can bond with an ambiguous atom is also ambiguous
(this spreads). Ambiguous atoms don't bond.
* Every unambiguous atom forms one bond with each of its possible partners, all
at the same time. Loose atoms that bond join the molecule.
* This repeats in rounds until no bond forms, adding a second, third or fourth
bond to pairs bonded earlier in the same step (double/triple/quadruple bonds).
That is one phase.
* Loose atoms that bonded during a phase join the molecule only once the phase
is over; then a new phase lets them bond with further loose atoms (chain
reaction). Phases repeat until the molecule stops growing. For example, with
H-c next to loose O-H, the C and O form a double bond first, which leaves the O
no free electrons, so the last H stays loose.

## Ions and electrons

* A positive ion is an atom with less free electrons than normal: each charge
is one less free electron. An ion is not neutral until its charge is gone.
* Electrons sit on cells; several can share one cell. When a molecule ion ends
a step next to a cell holding electrons, it captures one electron from that
cell (one per cell it touches), losing one charge and gaining one free electron.
Capture has its own ambiguity check, worked out like bonding's but separately
from it: a cell touching more molecule ions than it holds electrons is
ambiguous, and so is an ion touching more electron cells than its charge.
Anything that could capture from, or be captured by, an ambiguous ion or cell is
ambiguous too (this spreads). The other ions each capture one electron from
every cell they touch, all at the same time.
* Some atoms and electrons start on holes instead of level tiles.
