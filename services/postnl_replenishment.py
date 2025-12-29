# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields

_logger = logging.getLogger(__name__)


class PostNLReplenishmentService(models.AbstractModel):
    _name = "postnl.replenishment.service"
    _description = "PostNL Replenishment Service"

    def send_replenishment(self, replenishment):
        """
        replenishment: postnl.replenishment record
        Supports sending from purchase order OR incoming picking.
        """
        config = self.env["postnl.base.service"].get_config()

        # ✅ Get inbound URL from configuration (fallback safe)
        inbound_url = config.postnl_inbound_url or "https://api-sandbox.postnl.nl/v2/fulfilment/replenishment"

        po = replenishment.purchase_order_id
        picking = replenishment.picking_id

        # Dates
        if po:
            order_date = (po.date_order.date() if po.date_order else fields.Date.today()).isoformat()
            planned_date = (po.date_planned.date() if getattr(po, "date_planned", False) else fields.Date.today()).isoformat()
        elif picking:
            order_date = (picking.scheduled_date.date() if picking.scheduled_date else fields.Date.today()).isoformat()
            planned_date = (picking.scheduled_date.date() if picking.scheduled_date else fields.Date.today()).isoformat()
        else:
            order_date = fields.Date.today().isoformat()
            planned_date = fields.Date.today().isoformat()

        payload = {
            "orderNumber": replenishment.name,
            "merchantCode": replenishment.merchant_code,
            "fulfilmentLocation": replenishment.fulfilment_location,
            "orderDate": order_date,
            "plannedReceiptDate": planned_date,
            "orderLines": []
        }

        # Lines from PO
        if po:
            for line in po.order_line:
                product = line.product_id
                if not product or not product.default_code:
                    continue
                qty = int(line.product_qty or 0)
                if qty <= 0:
                    continue
                payload["orderLines"].append({
                    "SKU": product.default_code,
                    "quantity": qty,
                    "description": (product.name or "")[:35],
                })

        # Lines from picking (if provided)
        elif picking:
            for move in picking.move_ids_without_package:
                product = move.product_id
                if not product or not product.default_code:
                    continue
                qty = int(move.product_uom_qty or 0)
                if qty <= 0:
                    continue
                payload["orderLines"].append({
                    "SKU": product.default_code,
                    "quantity": qty,
                    "description": (product.name or "")[:35],
                })

        replenishment.request_payload = str(payload)

        headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key,
            "customerNumber": config.customer_number,
        }

        _logger.info("[PostNL Repl] → POST %s | %s", inbound_url, payload)

        response = requests.post(
            inbound_url,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code not in (200, 202):
            replenishment.state = "error"
            replenishment.response_message = response.text
            _logger.error("[PostNL Repl] ← (%s) %s", response.status_code, response.text)
            return False

        replenishment.state = "sent"
        replenishment.response_message = response.text
        _logger.info("[PostNL Repl] ← (%s) SENT for %s", response.status_code, replenishment.name)
        return True
