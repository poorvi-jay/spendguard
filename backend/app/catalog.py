import json
from functools import lru_cache
from typing import Optional

from app.config import CATALOG_PATH


@lru_cache(maxsize=1)
def _load() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text())


def search_products(query: str = "", max_price: Optional[float] = None) -> list[dict]:
    """Products matching any query word, best matches first. Agents search in phrases, not exact names."""
    words = [w for w in query.lower().split() if len(w) > 2]
    scored = []
    for product in _load():
        if max_price is not None and product["price"] > max_price:
            continue
        text = f"{product['name']} {product['description']} {product['category']}".lower()
        score = sum(w in text for w in words)
        if words and not score:
            continue
        scored.append((score, product))
    return [product for _, product in sorted(scored, key=lambda pair: -pair[0])]


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
