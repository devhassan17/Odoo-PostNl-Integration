# -*- coding: utf-8 -*-
import json
import logging
import re
from datetime import datetime

import requests

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

        ship_partner = order.partner_shipping_id or order.partner_id
        inv_partner = order.partner_invoice_id or order.partner_id

        order_number = _sanitize_ordernumber(order.name, order.id)
        order_dt = (order.date_order or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S")

        ship_street, ship_hn, ship_add = _split_street(ship_partner.street, ship_partner.street2)
        inv_street, inv_hn, inv_add = _split_street(inv_partner.street, inv_partner.street2)

        ship_fn, ship_ln = _split_name(ship_partner.name)
        inv_fn, inv_ln = _split_name(inv_partner.name)

        lines = []
        total_weight_kg = 0.0

        for l in order.order_line:
            p = l.product_id
            if not p or p.type == 'service':
                continue

            qty = int(l.product_uom_qty or 0)
            total_weight_kg += (p.weight or 0.0) * qty

            sku = (p.default_code or p.display_name or "").replace(" ", "").upper()
            if sku:
                lines.append({"SKU": sku, "quantity": qty})

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
