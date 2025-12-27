# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, _

_logger = logging.getLogger(__name__)


class PostNLReplenishmentService(models.AbstractModel):
    _name = "postnl.replenishment.service"
    _description = "PostNL Replenishment Service"

    POSTNL_REPLENISHMENT_URL = (
        "https://api-sandbox.postnl.nl/v2/fulfilment/replenishment"
    )

    def send_replenishment(self, picking):
        config = self.env["postnl.base.service"].get_config()

        payload = {
            "orderNumber": picking.name[:10],
            "merchantCode": config.merchant_code,
            "fulfilmentLocation": config.fulfilment_location,
            "orderDate": picking.scheduled_date.date().isoformat(),
            "plannedReceiptDate": picking.scheduled_date.date().isoformat(),
            "orderLines": []
        }

        for move in picking.move_ids_without_package:
            product = move.product_id
            if not product.default_code:
                continue

            payload["orderLines"].append({
                "SKU": product.default_code,
                "quantity": int(move.product_uom_qty),
                "description": product.name[:35],
            })

        headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key,
            "customerNumber": config.customer_number,
        }

        _logger.info("PostNL Inbound Payload: %s", payload)

        response = requests.post(
            self.POSTNL_REPLENISHMENT_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code not in (200, 202):
            _logger.error("PostNL Replenishment Error: %s", response.text)
            raise Exception(
                _("PostNL Replenishment failed (%s): %s")
                % (response.status_code, response.text)
            )

        _logger.info(
            "PostNL inbound sent successfully for picking %s",
            picking.name
        )

        return True
