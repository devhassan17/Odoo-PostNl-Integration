# -*- coding: utf-8 -*-
import json
import logging
import re
from datetime import datetime

import requests

from .. import postnl_config

_logger = logging.getLogger(__name__)


def _split_street(street: str, street2: str = ""):
    """Best-effort split of Odoo street into (street, houseNumber, addition).

    PostNL Order API requires street + houseNumber (NL/BE) and optional houseNumberAddition.
    """
    full = " ".join([s for s in [street, street2] if s])
    full = re.sub(r"\s+", " ", full).strip()
    # Patterns like: "Kaagschip 14 B" or "Main St 12A".
    m = re.match(r"^(.*?)(?:\s+(\d+))(?:\s*([A-Za-z0-9\-\/]+))?$", full)
    if not m:
        return full[:30], 0, ""
    st = (m.group(1) or "").strip()
    hn = int(m.group(2) or 0)
    add = (m.group(3) or "").strip()
    return st[:30], hn, add[:30]


def _split_name(name: str):
    name = (name or "").strip()
    if not name:
        return "", ""
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _sanitize_ordernumber(order_name: str, order_id: int):
    """PostNL restriction: cannot contain lowercase/spaces; max length 10; not letters only."""
    raw = (order_name or "").strip()
    raw = raw.replace(" ", "").upper()
    raw = re.sub(r"[^A-Z0-9\-]", "", raw)
    if not raw:
        raw = f"SO{order_id}"
    # Ensure not letters-only
    if raw.isalpha():
        raw = f"{raw[:8]}{order_id % 100:02d}"
    if len(raw) > 10:
        raw = raw[-10:]
    return raw


class PostNLClient:
    def __init__(self, env):
        self.env = env

    def _headers(self):
        # PostNL required header keys: Content-type, customerNumber, apikey
        api_key = self.env['ir.config_parameter'].sudo().get_param('postnl.api_key') or postnl_config.API_KEY
        customer_number = self.env['ir.config_parameter'].sudo().get_param('postnl.customer_number') or postnl_config.CUSTOMER_NUMBER
        return {
            "Content-Type": "application/json",
            "customerNumber": customer_number,
            "apikey": api_key,
        }

    def _get_param(self, key: str, default: str = ""):
        return self.env['ir.config_parameter'].sudo().get_param(key) or default

    def _get_product_code(self, order, total_weight_kg: float):
        """Pick PostNL productCode based on weight+destination country rules."""
        country = (order.partner_shipping_id.country_id or order.partner_id.country_id)
        if not country:
            return self._get_param('postnl.default_product_code', postnl_config.DEFAULT_PRODUCT_CODE)

        rules = self.env['postnl.shipping.rule'].sudo().search([
            ('active', '=', True),
            ('country_ids', 'in', [country.id]),
            ('max_weight_kg', '>=', total_weight_kg),
        ], order='max_weight_kg asc', limit=1)
        if rules:
            return rules.product_code

        return self._get_param('postnl.default_product_code', postnl_config.DEFAULT_PRODUCT_CODE)

    def send_sale_order(self, order):
        """Send sale.order to PostNL Fulfilment Order API."""
        order.ensure_one()

        ship_partner = order.partner_shipping_id or order.partner_id
        inv_partner = order.partner_invoice_id or order.partner_id

        # Optional allowlist
        if postnl_config.ALLOWED_COUNTRY_CODES:
            cc = (ship_partner.country_id.code or "").upper() if ship_partner.country_id else ""
            if cc not in [c.upper() for c in postnl_config.ALLOWED_COUNTRY_CODES]:
                _logger.info("[PostNL] Skip order %s (country %s not allowed)", order.name, cc)
                return True

        order_number = _sanitize_ordernumber(order.name, order.id)
        order_dt = order.date_order or datetime.utcnow()
        order_dt_str = order_dt.strftime("%Y-%m-%dT%H:%M:%S")

        ship_street, ship_hn, ship_add = _split_street(ship_partner.street or "", ship_partner.street2 or "")
        inv_street, inv_hn, inv_add = _split_street(inv_partner.street or "", inv_partner.street2 or "")

        ship_fn, ship_ln = _split_name(ship_partner.name)
        inv_fn, inv_ln = _split_name(inv_partner.name)

        lines = []
        total_weight_kg = 0.0
        for l in order.order_line:
            p = l.product_id
            if not p or p.type == 'service':
                continue
            qty = float(l.product_uom_qty or 0.0)
            if p.weight:
                total_weight_kg += float(p.weight) * qty
            sku = (p.default_code or "").strip() or (p.display_name or "").strip()
            if not sku:
                continue
            # PostNL restriction for SKU: no lowercase/spaces (doc says no lowercase/spaces for article numbers)
            sku_norm = sku.replace(" ", "").upper()
            lines.append({
                "SKU": sku_norm,
                "quantity": int(qty),
            })

        if not lines:
            _logger.info("[PostNL] Skip order %s (no shippable lines)", order.name)
            return True

        merchant_code = self._get_param('postnl.merchant_code', postnl_config.MERCHANT_CODE)
        fulfilment_location = self._get_param('postnl.fulfilment_location', postnl_config.FULFILMENT_LOCATION)
        channel = self._get_param('postnl.channel', postnl_config.CHANNEL)
        product_code = self._get_product_code(order, total_weight_kg)

        payload = {
            "orderNumber": order_number,
            "webOrderNumber": order_number,
            "merchantCode": merchant_code,
            "fulfilmentLocation": fulfilment_location,
            "channel": channel,
            "productCode": product_code,
            "orderDateTime": order_dt_str,
            "orderLines": lines,
            "shipToAddress": {
                "firstName": ship_fn,
                "lastName": ship_ln or ship_fn,
                "companyName": ship_partner.commercial_company_name or ship_partner.company_name or "",
                "street": ship_street,
                "houseNumber": ship_hn or 0,
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
                "houseNumber": inv_hn or 0,
                "houseNumberAddition": inv_add,
                "postalCode": (inv_partner.zip or "").replace(" ", ""),
                "city": inv_partner.city or "",
                "countryCode": inv_partner.country_id.code or "",
                "phoneNumber": inv_partner.phone or inv_partner.mobile or "",
                "email": inv_partner.email or "",
            },
        }

        url = self._get_param('postnl.api_url', postnl_config.API_URL)
        headers = self._headers()

        # Create technical log row
        log_rec = self.env['postnl.order.log'].sudo().create({
            'sale_order_id': order.id,
            'order_name': order.name,
            'destination_country_id': ship_partner.country_id.id if ship_partner.country_id else False,
            'total_weight_kg': total_weight_kg,
            'product_code': product_code,
            'endpoint_url': url,
            'request_payload': json.dumps(payload, ensure_ascii=False),
        })

        # Create an ir.logging entry before request (no API key logged)
        self.env['ir.logging'].sudo().create({
            'name': f"PostNL Order {order.name}",
            'type': 'server',
            'level': 'INFO',
            'message': f"Sending order {order.name} to PostNL | url={url} | orderNumber={order_number}",
            'path': 'postnl_fulfilment_integration',
            'func': 'send_sale_order',
            'line': 0,
        })

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=postnl_config.TIMEOUT)
            status = resp.status_code
            try:
                body = resp.json()
            except Exception:
                body = {'raw': (resp.text or '')[:2000]}

            log_rec.sudo().write({
                'http_status': status,
                'success': True if 200 <= status < 300 else False,
                'response_body': json.dumps(body, ensure_ascii=False)[:5000],
                'error_message': False if 200 <= status < 300 else (resp.text or '')[:255],
            })

            level = 'INFO' if 200 <= status < 300 else 'ERROR'
            msg = f"PostNL response for {order.name}: HTTP {status} | {json.dumps(body)[:1800]}"

            self.env['ir.logging'].sudo().create({
                'name': f"PostNL Order {order.name}",
                'type': 'server',
                'level': level,
                'message': msg,
                'path': 'postnl_fulfilment_integration',
                'func': 'send_sale_order',
                'line': 0,
            })

            if 200 <= status < 300:
                _logger.info("[PostNL] Sent order %s successfully (HTTP %s)", order.name, status)
                return True
            _logger.error("[PostNL] Failed to send order %s (HTTP %s)", order.name, status)
            return False

        except Exception as e:
            _logger.exception("[PostNL] Exception sending order %s: %s", order.name, e)
            log_rec.sudo().write({
                'success': False,
                'http_status': 0,
                'error_message': str(e)[:255],
            })
            self.env['ir.logging'].sudo().create({
                'name': f"PostNL Order {order.name}",
                'type': 'server',
                'level': 'ERROR',
                'message': f"PostNL request exception for {order.name}: {str(e)}",
                'path': 'postnl_fulfilment_integration',
                'func': 'send_sale_order',
                'line': 0,
            })
            return False
