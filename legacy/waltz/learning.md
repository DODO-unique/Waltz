Forward references in type hints

When a type is referenced before it has been defined, Python cannot resolve its name during class creation.

Example:

class A:
    def create(self) -> "B":
        ...

class B:
    ...

The quotes make "B" a forward reference, telling Python to resolve it later.

Alternatively, use:

from __future__ import annotations

This postpones evaluation of all type annotations, allowing you to write:

def create(self) -> B:
    ...

without quotes.


* async def foo(...) -> T means calling foo returns Awaitable[T].
* The function object itself is typed as Callable[..., Awaitable[T]].
* Only annotate Awaitable or Coroutine when you're talking about the result of calling an async function, not the function object itself.