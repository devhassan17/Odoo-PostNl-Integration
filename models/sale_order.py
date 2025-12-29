# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

from ..services.postnl_client import PostNLClient

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    postnl_last_send = fields.Datetime(copy=False, readonly=True)
    postnl_last_result = fields.Char(copy=False, readonly=True)

    def action_confirm(self):
        res = super().action_confirm()

        # PostNL config (singleton)
        config = self.env["postnl.config"].search([], limit=1)
        allowed_companies = config.allowed_company_ids if config else self.env["res.company"]

        for order in self:
            # ✅ company filter (SAFE DEFAULT: if allowed list empty -> skip)
            if not config or not allowed_companies or order.company_id not in allowed_companies:
                _logger.info(
                    "[PostNL] Skipping %s (company=%s) not in allowed companies",
                    order.name, order.company_id.name
                )
                continue

            try:
                client = PostNLClient(order.env)
                ok = client.send_sale_order(order)
                order.write({
                    "postnl_last_send": fields.Datetime.now(),
                    "postnl_last_result": "success" if ok else "error",
                })
            except Exception as e:
                _logger.exception("[PostNL] Unexpected error in action_confirm for %s: %s", order.name, e)
                order.write({
                    "postnl_last_send": fields.Datetime.now(),
                    "postnl_last_result": f"exception: {str(e)}",
                })
                order.env["ir.logging"].sudo().create({
                    "name": f"PostNL Order {order.name}",
                    "type": "server",
                    "level": "ERROR",
                    "message": f"Unexpected exception after confirm for {order.name}: {str(e)}",
                    "path": "postnl_fulfilment_integration",
                    "func": "action_confirm",
                    "line": 0,
                })

        return res
