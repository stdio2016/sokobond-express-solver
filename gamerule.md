# Sokobond express rule

* The drawn path starts on the player's atom and ends on the exit. It stays
on level tiles and can't pass through the same tile twice.
* The molecule slides one tile per path step. Atoms attached to it may hang
outside the level while moving, but must all be inside it at the end.
* Any molecule atom with a free electron that ends a step next to another
atom with a free electron bonds with it, pulling it (and
whatever it's bonded to) into the molecule.
* A molecule atom may never move into a tile holding another atom.
* To win, every atom must be neutral and use up all its free electrons.
* Start point has a leaving direction restricting the first move, and end point also has a entering direction restricting the final move.
* Cannot draw path past any initial atoms, start point, end point.
* When adjacent atoms have multiple free electrons, they bond multiple bonds.