import base64
from odoo import http
from odoo.http import request

class PostNLController(http.Controller):

    @http.route('/postnl/label/<int:shipment_id>', type='http', auth='user')
    def download_label(self, shipment_id, **kw):
        shipment = request.env['postnl.shipment'].browse(shipment_id).sudo()
        if not shipment or not shipment.exists():
            return request.not_found()
        if not shipment.label_pdf:
            return request.not_found()
        pdf = base64.b64decode(shipment.label_pdf)
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="PostNL_Label_%s.pdf"' % (shipment.barcode or shipment.name)),
        ]
        return request.make_response(pdf, headers=headers)

    @http.route('/postnl/options', type='json', auth='public', website=True, csrf=False)
    def delivery_options(self, **kwargs):
        # In real life, call PostNL Timeframe API based on address & cut-off
        # Here we just emulate options
        return {
            "options": [
                {"code": "standard", "label": "Standard Delivery (Next day)"},
                {"code": "morning", "label": "Morning Delivery"},
                {"code": "evening", "label": "Evening Delivery"},
                {"code": "pickup", "label": "Pickup Point"},
            ]
        }

    @http.route('/postnl/pickups', type='json', auth='public', website=True, csrf=False)
    def pickup_points(self, **kwargs):
        # Emulate pickup locations. Replace with Locations API.
        postcode = (kwargs.get("postcode") or "").upper().replace(" ", "")
        return {"pickups": [
            {"code": "PK001", "name": "PostNL Point Centrum", "address": "Mainstreet 1", "postcode": postcode or "1011AB", "city": "Amsterdam"},
            {"code": "PK002", "name": "Supermarkt West", "address": "Westlaan 12", "postcode": postcode or "1012CD", "city": "Amsterdam"},
        ]}
