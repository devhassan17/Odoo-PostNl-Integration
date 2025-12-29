# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super().button_confirm()

        config = self.env["postnl.config"].search([], limit=1)
        if not config:
            _logger.warning("[PostNL Repl] Config missing, skipping replenishment creation.")
            return res

        for po in self:
            # Prevent duplicates
            exists = self.env["postnl.replenishment"].search(
                [("purchase_order_id", "=", po.id)],
                limit=1
            )
            if exists:
                continue

            replenishment = self.env["postnl.replenishment"].create({
                "name": po.name,
                "purchase_order_id": po.id,
                "merchant_code": config.merchant_code,
                "fulfilment_location": config.fulfilment_location,
            })

            try:
                self.env["postnl.replenishment.service"].send_replenishment(replenishment)
            except Exception as e:
                _logger.error("[PostNL Repl] Failed for PO %s: %s", po.name, str(e))

        return res
