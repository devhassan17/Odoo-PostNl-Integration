# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class PostNLFulfilmentReceiver(http.Controller):

    @http.route("/postnl/fulfilment/shipment", type="http", auth="public", csrf=False, methods=["POST"])
    def receive_shipment(self, **kwargs):
        # security header (PDF: webhook uses apikey provided by client)
        incoming_key = request.httprequest.headers.get("apikey", "")
        expected_key = request.env["ir.config_parameter"].sudo().get_param("postnl_base.fulfilment_webhook_key") or ""
        if expected_key and incoming_key != expected_key:
            return request.make_response("Unauthorized", headers=[("Content-Type", "text/plain")], status=401)

        try:
            raw = request.httprequest.data.decode("utf-8") if request.httprequest.data else "{}"
            payload = json.loads(raw)
        except Exception as e:
            _logger.exception("Invalid JSON: %s", e)
            return request.make_response("Bad Request", headers=[("Content-Type", "text/plain")], status=400)

        request.env["postnl.fulfilment.shipment.queue"].sudo().create_from_webhook(payload)
        return request.make_response("OK", headers=[("Content-Type", "text/plain")], status=200)
