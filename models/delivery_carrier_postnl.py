from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("postnl", "PostNL")])
    postnl_wbs_rule_id = fields.Many2one("postnl.wbs.rule", string="Default WBS Rule")

    def _postnl_client(self):
        return self.env["postnl.client"].sudo()

    def rate_shipment(self, order):
        self.ensure_one()
        if self.delivery_type != "postnl":
            return super().rate_shipment(order)
        # Basic flat/fallback. You can use WBS rules or API here.
        # Example: find rule by country & weight and maybe set price
        country_code = order.partner_shipping_id.country_id.code or "NL"
        weight = sum(order.order_line.mapped("product_uom_qty"))  # naive; replace with package weight
        rule = self.postnl_wbs_rule_id or self.env["postnl.wbs.rule"].search([], limit=1)
        price = self._compute_price_by_rule(rule, country_code, weight) if rule else 0.0
        return {"success": True, "price": price, "error_message": False, "warning_message": False}

    def _compute_price_by_rule(self, rule, country_code, weight):
        # Placeholder pricing: implement as needed
        return 0.0

    def send_shipping(self, pickings):
        # Called from picking -> Put in pack -> Validate
        res = []
        client = self._postnl_client()
        if not client.is_configured():
            raise UserError(_("PostNL is not configured. Fill settings first."))
        for picking in pickings:
            shipment = self.env["postnl.shipment"].create({
                "picking_id": picking.id,
                "package_type": "package",
            })
            shipment._create_or_fetch_label()
            result = {
                "exact_price": 0.0,
                "tracking_number": shipment.barcode,
            }
            res.append(result)
        return res

    def get_tracking_link(self, picking):
        if picking.carrier_tracking_ref:
            client = self._postnl_client()
            return client.build_track_trace_url(picking.carrier_tracking_ref, picking.partner_id)
        return False
