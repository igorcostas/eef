from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Node:
    state: Any
    parent: Optional['Node'] = None
    action: Any = None
    g: float = 0.0
    h: float = 0.0

    @property
    def f(self):  # type: () -> float
        return self.g + self.h

    def path(self):  # type: () -> List[Node]
        nodes = []
        current = self
        while current is not None:
            nodes.append(current)
            current = current.parent
        nodes.reverse()
        return nodes
