from typing import AsyncGenerator, List


async def _async_generator(values: List) -> AsyncGenerator:
    """Async generator."""
    for value in values:
        yield value
