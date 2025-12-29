# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class PostNLReplenishmentService(models.AbstractModel):
    _name = "postnl.replenishment.service"
    _description = "PostNL Replenishment Service"

    POSTNL_REPLENISHMENT_URL = (
        "https://api-sandbox.postnl.nl/v2/fulfilment/replenishment"
    )

    def send_replenishment(self, replenishment):
        """
        replenishment = postnl.replenishment record
        """
        config = self.env["postnl.base.service"].get_config()
        picking = replenishment.picking_id

        payload = {
            "orderNumber": replenishment.name,
            "merchantCode": replenishment.merchant_code,
            "fulfilmentLocation": replenishment.fulfilment_location,
            "orderDate": fields.Date.today().isoformat(),
            "plannedReceiptDate": fields.Date.today().isoformat(),
            "orderLines": []
        }

        for move in picking.move_ids_without_package:
            product = move.product_id
            if not product.default_code:
                _logger.warning(
                    "Skipping product without SKU: %s", product.name
                )
                continue

            payload["orderLines"].append({
                "SKU": product.default_code,
                "quantity": int(move.product_uom_qty),
                "description": product.name[:35],
            })

        replenishment.request_payload = str(payload)

        headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key,
            "customerNumber": config.customer_number,
        }

        _logger.info(
            "PostNL Replenishment SEND [%s]: %s",
            replenishment.name,
            payload,
        )

        response = requests.post(
            self.POSTNL_REPLENISHMENT_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code not in (200, 202):
            replenishment.state = "error"
            replenishment.response_message = response.text

            _logger.error(
                "PostNL Replenishment ERROR [%s]: %s",
                replenishment.name,
                response.text,
            )
            return False

        replenishment.state = "sent"
        replenishment.response_message = response.text

        _logger.info(
            "PostNL Replenishment SENT [%s]",
            replenishment.name,
        )

        return True
