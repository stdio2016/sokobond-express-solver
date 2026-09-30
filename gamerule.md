# Sokobond express rule

* The drawn path starts on the player's atom and ends on the exit. It stays
on level tiles and can't pass through the same tile twice.
* The molecule slides one tile per path step. Atoms attached to it may hang
outside the level while moving, but must all be inside it at the end.
* Any molecule atom with a free electron that ends a step next to another
atom with a free electron bonds with it, pulling it (and
whatever it's bonded to) into the molecule.
* A molecule atom may never move into a tile holding another atom or electrons.
* To win, every atom must be neutral and use up all its free electrons.
* Start point has a leaving direction restricting the first move, and end point also has a entering direction restricting the final move.
Since the first move is forced, it is taken automatically: the tile it leads to
becomes part of the path (an obstacle like the start) and drawing begins there.
It is not counted as a move.
* Cannot draw path past any initial atoms, initial electrons, start point, end point.
* When adjacent atoms have multiple free electrons, they bond multiple bonds.
* A positive ion is an atom with less free electrons than normal: each charge
is one less free electron. An ion is not neutral until its charge is gone.
* Electrons sit on cells; several can share one cell. When a molecule ion ends
a step next to a cell holding electrons, it captures one electron from that
cell (one per cell it touches), losing one charge and gaining one free electron.
Capturing happens before bonding, so the new free electron can bond in the same step.
* Some atoms and electrons start on holes instead of level tiles.
