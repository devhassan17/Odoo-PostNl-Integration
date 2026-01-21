# -*- coding: utf-8 -*-
import re


def normalize_sku(value: str) -> str:
    """Normalize SKU similar to Monta style: remove spaces, uppercase, keep safe chars."""
    value = (value or "").strip().replace(" ", "").upper()
    value = re.sub(r"[^A-Z0-9\-_]", "", value)
    return value


def resolve_sku(product) -> str:
    """
    Resolve SKU with Monta-like priority:
    1) product.monta_sku (if field exists)
    2) product.default_code
    3) first vendor code (seller_ids.product_code)
    4) product.barcode
    5) product.product_tmpl_id.default_code
    Fallback: display_name
    """
    if not product:
        return ""

    # 1) monta_sku (optional field)
    try:
        if hasattr(product, "_fields") and "monta_sku" in product._fields:
            sku = product.monta_sku
            if sku:
                return normalize_sku(sku)
    except Exception:
        pass

    # 2) default_code
    sku = getattr(product, "default_code", "") or ""
    if sku:
        return normalize_sku(sku)

    # 3) vendor product_code
    try:
        sellers = getattr(product, "seller_ids", None)
        if sellers:
            seller = sellers[:1]
            if seller and seller.product_code:
                return normalize_sku(seller.product_code)
    except Exception:
        pass

    # 4) barcode
    sku = getattr(product, "barcode", "") or ""
    if sku:
        return normalize_sku(sku)

    # 5) template default_code
    try:
        tmpl = getattr(product, "product_tmpl_id", None)
        if tmpl and getattr(tmpl, "default_code", None):
            return normalize_sku(tmpl.default_code)
    except Exception:
        pass

    # fallback
    name = getattr(product, "display_name", "") or ""
    return normalize_sku(name)
