# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        """
        Automatically send inbound to PostNL when Incoming Shipment is validated
        """
        res = super().button_validate()

        for picking in self:
            if (
                picking.picking_type_id.code == "incoming"
                and picking.state == "done"
            ):
                try:
                    service = (
                        self.env["postnl.base.service"]
                        .get_replenishment_service()
                    )
                    service.send_replenishment(picking)
                except Exception as e:
                    _logger.error(
                        "PostNL inbound failed for %s: %s",
                        picking.name,
                        str(e)
                    )
                    # ❗ Do NOT block stock validation
                    # Stock is more important than API sync

        return res
