"""Runtime compatibility shims. Imported for side effects by ``common/__init__``.

``dronekit`` 2.9.2 (the last PyPI release, 2015) references the ``collections``
ABCs that were moved to ``collections.abc`` in Python 3.3 and removed from
``collections`` in Python 3.10, so ``import dronekit`` raises ``AttributeError``
on our interpreter (3.12). Re-exposing the names on ``collections`` before
dronekit is first imported works around it.

TODO(drone-port): delete this once the project moves to a maintained / typed
MAVLink library or drops the dronekit dependency. Tracked in the dronekit
compatibility discussion.
"""

import collections
import collections.abc

_MOVED_ABCS = (
    "Callable",
    "Hashable",
    "Iterable",
    "Iterator",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Sequence",
    "Set",
)

for _name in _MOVED_ABCS:
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))
