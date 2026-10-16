import json
from functools import lru_cache
from typing import Optional

from app.config import CATALOG_PATH


@lru_cache(maxsize=1)
def _load() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text())


def search_products(query: str = "", max_price: Optional[float] = None) -> list[dict]:
    query = query.lower().strip()
    results = []
    for product in _load():
        if query and query not in product["name"].lower() and query not in product["description"].lower():
            continue
        if max_price is not None and product["price"] > max_price:
            continue
        results.append(product)
    return results


def get_product(product_id: str) -> Optional[dict]:
    for product in _load():
        if product["id"] == product_id:
            return product
    return None


def cheaper_alternative(product: dict, max_price: float) -> Optional[dict]:
    """Find the closest-priced alternative in the same category that fits under max_price."""
    candidates = [
        p
        for p in _load()
        if p["category"] == product["category"] and p["id"] != product["id"] and p["price"] <= max_price
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p["price"])
