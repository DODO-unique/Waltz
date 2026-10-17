from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import Generic, TypeVar

P = TypeVar("P")
R = TypeVar("R")

@dataclass(frozen=True)
class OperationIntentions(Generic[P, R]):
    operation: Enum
    payload: type[P] | UnionType