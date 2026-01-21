# -*- coding: utf-8 -*-
import json
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class PostNLFulfilmentShipmentQueue(models.Model):
    _name = "postnl.fulfilment.shipment.queue"
    _description = "PostNL Fulfilment Shipment Queue"
    _order = "create_date desc"

    state = fields.Selection([
        ("new", "New"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ], default="new", required=True, index=True)

    attempts = fields.Integer(default=0)
    last_error = fields.Text()

    payload = fields.Text(required=True)  # full JSON string
    message_no = fields.Char(index=True)
    merchant_code = fields.Char(index=True)
    event_date = fields.Char()
    event_time = fields.Char()

    def _parse_payload(self):
        self.ensure_one()
        return json.loads(self.payload or "{}")

    @api.model
    def create_from_webhook(self, payload_dict: dict):
        meta = {
            "merchantCode": payload_dict.get("merchantCode"),
            "messageNo": payload_dict.get("messageNo"),
            "date": payload_dict.get("date"),
            "time": payload_dict.get("time"),
        }
        return self.create({
            "payload": json.dumps(payload_dict),
            "merchant_code": meta["merchantCode"],
            "message_no": meta["messageNo"],
            "event_date": meta["date"],
            "event_time": meta["time"],
        })
