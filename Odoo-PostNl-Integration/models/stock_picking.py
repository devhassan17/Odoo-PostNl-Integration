# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_done(self):
        res = super().action_done()

        for picking in self:
            if (
                picking.picking_type_id.code != "incoming"
                or picking.state != "done"
            ):
                continue

            if self.env["postnl.replenishment"].search([
                ("picking_id", "=", picking.id)
            ], limit=1):
                continue

            config = self.env["postnl.config"].search([], limit=1)
            if not config:
                _logger.warning("PostNL config missing, skipping replenishment")
                continue

            replenishment = self.env["postnl.replenishment"].create({
                "name": picking.name,
                "picking_id": picking.id,
                "merchant_code": config.merchant_code,
                "fulfilment_location": config.fulfilment_location,
            })

            try:
                self.env["postnl.replenishment.service"].send_replenishment(
                    replenishment
                )
            except Exception as e:
                _logger.error(
                    "PostNL replenishment failed for %s: %s",
                    picking.name,
                    str(e),
                )
                # IMPORTANT: never block stock validation

        return res
