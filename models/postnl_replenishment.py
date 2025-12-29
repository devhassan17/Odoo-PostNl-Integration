# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class PostNLReplenishment(models.Model):
    _name = "postnl.replenishment"
    _description = "PostNL Replenishment"
    _order = "create_date desc"

    name = fields.Char(string="Replenishment Number", required=True)
    picking_id = fields.Many2one("stock.picking", required=True, ondelete="cascade")

    merchant_code = fields.Char(required=True)
    fulfilment_location = fields.Char(required=True)

    state = fields.Selection([
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("error", "Error"),
    ], default="draft")

    request_payload = fields.Text()
    response_message = fields.Text()

    def action_send_to_postnl(self):
        config = self.env["postnl.config"].search([], limit=1)
        if not config:
            raise Exception("PostNL configuration missing")

        payload = {
            "orderNumber": self.name[:10],
            "merchantCode": self.merchant_code,
            "fulfilmentLocation": self.fulfilment_location,
            "orderDate": fields.Date.today().isoformat(),
            "plannedReceiptDate": fields.Date.today().isoformat(),
            "orderLines": []
        }

        for move in self.picking_id.move_ids_without_package:
            product = move.product_id
            if not product.default_code:
                continue

            payload["orderLines"].append({
                "SKU": product.default_code,
                "quantity": int(move.product_uom_qty),
                "description": product.name[:35],
            })

        self.request_payload = str(payload)

        headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key,
            "customerNumber": config.customer_number,
        }

        _logger.info("PostNL Replenishment SEND: %s", payload)

        response = requests.post(
            "https://api-sandbox.postnl.nl/v2/fulfilment/replenishment",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code not in (200, 202):
            self.state = "error"
            self.response_message = response.text
            _logger.error("PostNL Replenishment ERROR: %s", response.text)
            return False

        self.state = "sent"
        self.response_message = response.text
        _logger.info("PostNL Replenishment SENT: %s", self.name)
        return True
