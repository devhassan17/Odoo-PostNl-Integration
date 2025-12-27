# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        """
        Auto-send inbound replenishment to PostNL on validation
        """
        res = super().button_validate()

        for picking in self:
            if (
                picking.picking_type_id.code == "incoming"
                and picking.state == "done"
            ):
                try:
                    self.env["postnl.replenishment.service"].send_replenishment(
                        picking
                    )
                except Exception as e:
                    _logger.error(
                        "PostNL inbound failed for %s: %s",
                        picking.name,
                        str(e)
                    )
                    # Do NOT block stock validation

        return res
