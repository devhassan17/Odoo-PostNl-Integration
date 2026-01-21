# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class PostNLReplenishment(models.Model):
    _name = "postnl.replenishment"
    _description = "PostNL Replenishment"
    _order = "create_date desc"

    name = fields.Char(string="Replenishment Number", required=True)

    # NEW: link to PO (so PO confirm can create replenishment)
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order", ondelete="cascade")

    # OPTIONAL: link to receipt if you want later
    picking_id = fields.Many2one("stock.picking", string="Incoming Receipt", ondelete="cascade")

    merchant_code = fields.Char(required=True)
    fulfilment_location = fields.Char(required=True)

    state = fields.Selection([
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("error", "Error"),
    ], default="draft")

    request_payload = fields.Text()
    response_message = fields.Text()
