# -*- coding: utf-8 -*-
import math
import logging

_logger = logging.getLogger(__name__)


def _ceil_qty(qty: float) -> int:
    """Shipping systems usually want integer qty. If qty is fractional, round UP."""
    if qty is None:
        return 0
    try:
        if float(qty).is_integer():
            return int(qty)
        return int(math.ceil(float(qty)))
    except Exception:
        return int(qty or 0)


def _get_phantom_bom(env, product):
    """Find phantom BoM for product/product template (if mrp installed)."""
    if "mrp.bom" not in env:
        return None

    Bom = env["mrp.bom"].sudo()
    domain = [
        ("type", "=", "phantom"),
        ("active", "=", True),
        ("product_tmpl_id", "=", product.product_tmpl_id.id),
    ]

    # Prefer variant-specific BoM if exists
    boms = Bom.search(domain + [("product_id", "=", product.id)], limit=1)
    if boms:
        return boms

    # Fallback template-level BoM
    boms = Bom.search(domain + [("product_id", "=", False)], limit=1)
    return boms or None


def _get_oca_pack_lines(env, product):
    """
    OCA product_pack commonly uses model: product.pack.line
    Fields often: parent_product_id, product_id, quantity
    """
    if "product.pack.line" not in env:
        return env["ir.model"]  # dummy empty-like (won't be used)

    PackLine = env["product.pack.line"].sudo()
    return PackLine.search([("parent_product_id", "=", product.id)])


def explode_product(env, product, qty, visited=None):
    """
    Returns list of tuples: [(leaf_product, leaf_qty_float), ...]
    Expands packs/kits using:
    - phantom BoM (mrp.bom type phantom)
    - OCA product_pack (product.pack.line)
    """
    visited = visited or set()

    if not product:
        return []

    # Prevent recursion loops
    key = (product._name, product.id)
    if key in visited:
        _logger.warning("[PostNL][PACK] Recursion detected for product %s, skipping deeper expansion.", product.display_name)
        return [(product, qty)]
    visited.add(key)

    # 1) Phantom BoM explode
    bom = _get_phantom_bom(env, product)
    if bom:
        result = []
        bom_qty = float(bom.product_qty or 1.0)
        factor = (float(qty or 0.0) / bom_qty) if bom_qty else float(qty or 0.0)

        for bl in bom.bom_line_ids:
            comp = bl.product_id
            comp_qty = float(bl.product_qty or 0.0) * factor
            result.extend(explode_product(env, comp, comp_qty, visited=visited))
        return result

    # 2) OCA product_pack explode (if present)
    try:
        if "product.pack.line" in env:
            pack_lines = _get_oca_pack_lines(env, product)
            if pack_lines:
                result = []
                for pl in pack_lines:
                    comp = pl.product_id
                    comp_qty = float(pl.quantity or 0.0) * float(qty or 0.0)
                    result.extend(explode_product(env, comp, comp_qty, visited=visited))
                return result
    except Exception:
        pass

    # Leaf product
    return [(product, qty)]


def explode_sale_order_line(env, sale_line):
    """Convenience: explode a sale.order.line into leaf components with qty."""
    p = sale_line.product_id
    qty = float(sale_line.product_uom_qty or 0.0)
    return explode_product(env, p, qty)
