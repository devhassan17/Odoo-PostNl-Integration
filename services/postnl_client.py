# -*- coding: utf-8 -*-
import json
import logging
import math
import re
from datetime import datetime

import requests

from ..utils.sku import resolve_sku
from ..utils.pack import explode_sale_order_line

_logger = logging.getLogger(__name__)


def _split_street(street: str, street2: str = ""):
    """Best-effort split of Odoo street into (street, houseNumber, addition)."""
    full = " ".join([s for s in [street, street2] if s])
    full = re.sub(r"\s+", " ", full).strip()
    m = re.match(r"^(.*?)(?:\s+(\d+))(?:\s*([A-Za-z0-9\-\/]+))?$", full)
    if not m:
        return full[:30], 0, ""
    return (m.group(1) or "").strip()[:30], int(m.group(2) or 0), (m.group(3) or "")[:30]


def _split_name(name: str):
    name = (name or "").strip()
    if not name:
        return "", ""
    parts = name.split()
    return parts[0], " ".join(parts[1:]) if len(parts) > 1 else ""


def _sanitize_ordernumber(order_name: str, order_id: int):
    raw = (order_name or "").replace(" ", "").upper()
    raw = re.sub(r"[^A-Z0-9\-]", "", raw)
    if not raw:
        raw = f"SO{order_id}"
    if raw.isalpha():
        raw = f"{raw[:8]}{order_id % 100:02d}"
    return raw[-10:]


def _ceil_qty(qty: float) -> int:
    """If qty is fractional, round UP to avoid under-shipping."""
    if qty is None:
        return 0
    try:
        if float(qty).is_integer():
            return int(qty)
        return int(math.ceil(float(qty)))
    except Exception:
        return int(qty or 0)


class PostNLClient:

    def __init__(self, env):
        self.env = env
        self.icp = env['ir.config_parameter'].sudo()

    # ------------------------------------------------
    # CONFIG HELPERS (FROM UI ONLY)
    # ------------------------------------------------

    def _get_param(self, key, default=""):
        return self.icp.get_param(key, default)

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "customerNumber": self._get_param('postnl.customer_number'),
            "apikey": self._get_param('postnl.api_key'),
        }

    def _validate_config(self):
        missing = []
        if not self._get_param('postnl.api_url'):
            missing.append("API URL")
        if not self._get_param('postnl.api_key'):
            missing.append("API Key")
        if not self._get_param('postnl.customer_number'):
            missing.append("Customer Number")
        if missing:
            raise ValueError(f"PostNL configuration missing: {', '.join(missing)}")

    # ------------------------------------------------
    # URL GUARD (INSTANCE CHECK)
    # ------------------------------------------------
    def _is_instance_allowed(self):
        """
        If postnl.allowed_base_urls is empty => allow.
        Otherwise web.base.url must match one of the allowed URLs (comma-separated).
        """
        web_url = (self.icp.get_param("web.base.url") or "").strip()
        web_url = web_url.rstrip("/") + "/"

        allowed = (self.icp.get_param("postnl.allowed_base_urls") or "").strip()
        if not allowed:
            return True

        allowed_urls = [
            u.strip().rstrip("/") + "/"
            for u in allowed.split(",")
            if u.strip()
        ]

        is_ok = web_url.lower() in [u.lower() for u in allowed_urls]
        if not is_ok:
            _logger.warning("[PostNL Guard] BLOCKED. web.base.url=%s allowed=%s", web_url, allowed_urls)
        return is_ok

    # ------------------------------------------------
    # PRODUCT CODE (WEIGHT RULES)
    # ------------------------------------------------

    def _get_product_code(self, order, total_weight_kg):
        country = order.partner_shipping_id.country_id or order.partner_id.country_id
        if not country:
            return self._get_param('postnl.default_product_code')

        rule = self.env['postnl.shipping.rule'].sudo().search([
            ('active', '=', True),
            ('country_ids', 'in', country.id),
            ('max_weight_kg', '>=', total_weight_kg),
        ], order='max_weight_kg asc', limit=1)

        return rule.product_code if rule else self._get_param('postnl.default_product_code')

    # ------------------------------------------------
    # MAIN API CALL
    # ------------------------------------------------

    def send_sale_order(self, order):
        self._validate_config()
        order.ensure_one()

        # ✅ URL GUARD
        if not self._is_instance_allowed():
            # Keep logging in your existing order log model if available
            try:
                self.env['postnl.order.log'].sudo().create({
                    'sale_order_id': order.id,
                    'order_name': order.name,
                    'destination_country_id': (order.partner_shipping_id.country_id or order.partner_id.country_id).id,
                    'total_weight_kg': 0.0,
                    'product_code': '',
                    'endpoint_url': self._get_param('postnl.api_url'),
                    'request_payload': json.dumps({
                        'blocked': True,
                        'reason': 'Blocked by URL guard',
                        'web_base_url': self.icp.get_param("web.base.url"),
                        'allowed_base_urls': self.icp.get_param("postnl.allowed_base_urls"),
                    }, ensure_ascii=False),
                    'success': False,
                    'http_status': 0,
                    'error_message': 'Blocked by URL guard',
                })
            except Exception:
                pass
            return False

        ship_partner = order.partner_shipping_id or order.partner_id
        inv_partner = order.partner_invoice_id or order.partner_id

        order_number = _sanitize_ordernumber(order.name, order.id)
        order_dt = (order.date_order or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S")

        ship_street, ship_hn, ship_add = _split_street(ship_partner.street, ship_partner.street2)
        inv_street, inv_hn, inv_add = _split_street(inv_partner.street, inv_partner.street2)

        ship_fn, ship_ln = _split_name(ship_partner.name)
        inv_fn, inv_ln = _split_name(inv_partner.name)

        # Build order lines with pack expansion + Monta-like SKU resolver
        sku_qty_map = {}
        total_weight_kg = 0.0

        for l in order.order_line:
            p = l.product_id
            if not p or p.type == 'service':
                continue

            # explode packs/kits -> leaf components
            exploded = explode_sale_order_line(self.env, l)

            for leaf_product, leaf_qty_float in exploded:
                if not leaf_product or leaf_product.type == 'service':
                    continue

                qty_int = _ceil_qty(leaf_qty_float)
                if qty_int <= 0:
                    continue

                total_weight_kg += (leaf_product.weight or 0.0) * qty_int

                sku = resolve_sku(leaf_product)
                if not sku:
                    continue

                sku_qty_map[sku] = sku_qty_map.get(sku, 0) + qty_int

        lines = [{"SKU": sku, "quantity": qty} for sku, qty in sku_qty_map.items()]

        if not lines:
            _logger.info("[PostNL] Skip order %s (no shippable lines)", order.name)
            return True

        payload = {
            "orderNumber": order_number,
            "webOrderNumber": order_number,
            "merchantCode": self._get_param('postnl.merchant_code'),
            "fulfilmentLocation": self._get_param('postnl.fulfilment_location'),
            "channel": self._get_param('postnl.channel'),
            "productCode": self._get_product_code(order, total_weight_kg),
            "orderDateTime": order_dt,
            "orderLines": lines,
            "shipToAddress": {
                "firstName": ship_fn,
                "lastName": ship_ln or ship_fn,
                "street": ship_street,
                "houseNumber": ship_hn,
                "houseNumberAddition": ship_add,
                "postalCode": (ship_partner.zip or "").replace(" ", ""),
                "city": ship_partner.city or "",
                "countryCode": ship_partner.country_id.code or "",
                "phoneNumber": ship_partner.phone or ship_partner.mobile or "",
                "email": ship_partner.email or "",
            },
            "invoiceAddress": {
                "firstName": inv_fn,
                "lastName": inv_ln or inv_fn,
                "street": inv_street,
                "houseNumber": inv_hn,
                "houseNumberAddition": inv_add,
                "postalCode": (inv_partner.zip or "").replace(" ", ""),
                "city": inv_partner.city or "",
                "countryCode": inv_partner.country_id.code or "",
                "phoneNumber": inv_partner.phone or inv_partner.mobile or "",
                "email": inv_partner.email or "",
            },
        }

        url = self._get_param('postnl.api_url')
        timeout = int(self._get_param('postnl.timeout', '30'))

        log_rec = self.env['postnl.order.log'].sudo().create({
            'sale_order_id': order.id,
            'order_name': order.name,
            'destination_country_id': ship_partner.country_id.id,
            'total_weight_kg': total_weight_kg,
            'product_code': payload['productCode'],
            'endpoint_url': url,
            'request_payload': json.dumps(payload, ensure_ascii=False),
        })

        try:
            resp = requests.post(url, headers=self._headers(), json=payload, timeout=timeout)
            try:
                body = resp.json()
            except Exception:
                body = resp.text

            log_rec.write({
                'http_status': resp.status_code,
                'success': 200 <= resp.status_code < 300,
                'response_body': json.dumps(body, ensure_ascii=False)[:5000],
                'error_message': False if 200 <= resp.status_code < 300 else str(body)[:255],
            })

            if 200 <= resp.status_code < 300:
                _logger.info("[PostNL] Sent order %s successfully (HTTP %s)", order.name, resp.status_code)
                return True

            _logger.error("[PostNL] Failed to send order %s (HTTP %s)", order.name, resp.status_code)
            return False

        except Exception as e:
            _logger.exception("[PostNL] Exception sending order %s", order.name)
            log_rec.write({
                'success': False,
                'http_status': 0,
                'error_message': str(e)[:255],
            })
            return False
