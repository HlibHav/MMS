from math import ceil
from typing import Iterable, List, Tuple, TypeVar, Dict, Any

T = TypeVar("T")


def paginate_list(items: Iterable[T], page: int = 1, page_size: int = 20) -> Tuple[List[T], Dict[str, Any]]:
    """
    Slice an iterable and return pagination metadata.

    Returns a list (not generator) to avoid exhausting upstream iterables twice.
    """
    safe_page = max(1, page or 1)
    safe_size = max(1, min(page_size or 20, 100))
    materialized = list(items)
    total = len(materialized)
    start = (safe_page - 1) * safe_size
    end = start + safe_size
    sliced = materialized[start:end]
    meta = {
        "page": safe_page,
        "page_size": safe_size,
        "total": total,
        "total_pages": ceil(total / safe_size) if safe_size else 0,
    }
    return sliced, meta
