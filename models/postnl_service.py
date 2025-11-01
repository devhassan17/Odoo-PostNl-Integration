from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import base64

class PostnlService(models.AbstractModel):
    _name = "postnl.service"
    _description = "PostNL Service Layer (exports/imports)"
    _inherit = ["mail.thread"]

    def _export_orders_to_postnl(self, orders):
        self = self.sudo()
        count = 0
        for order in orders:
            try:
                if not order.shipping_code:
                    order._apply_shipping_rule()
                xml = self._build_order_xml(order)
                self._attach_payload(order, xml, fname=f"order_{order.name.replace('/', '_')}.xml")
                order.action_mark_exported()
                count += 1
            except Exception as e:
                order._post_single_error(str(e))
        return count

    def _import_shipments_update_orders(self):
        staged = self.env["postnl.order"].search([("state","=","exported")], limit=50)
        done = 0
        for rec in staged:
            try:
                if not rec.tracking_number:
                    rec.tracking_number = f"3S{rec.id:012d}NL"
                rec.action_mark_shipped()
                done += 1
            except Exception as e:
                rec._post_single_error(str(e))
        return done

    def _attach_payload(self, order, data, fname="payload.xml"):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.env["ir.attachment"].sudo().create({
            "name": fname,
            "res_model": order._name,
            "res_id": order.id,
            "type": "binary",
            "datas": base64.b64encode(data).decode("ascii"),
            "mimetype": "application/xml",
        })

    def _build_order_xml(self, order):
        partner = order.sale_id.partner_shipping_id
        lines = order.sale_id.order_line.filtered(lambda l: not l.display_type)
        ln_xml = "".join([
            f"""
            <line>
                <sku>{(ln.product_id.default_code or ln.product_id.barcode or ln.product_id.id)}</sku>
                <name>{(ln.name or '').replace('&','&amp;')}</name>
                <qty>{ln.product_uom_qty:.0f}</qty>
                <weight>{(ln.product_id.weight or 0.0):.3f}</weight>
            </line>
            """ for ln in lines
        ])
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<deliveryOrder>
  <header>
    <reference>{order.name}</reference>
    <shippingCode>{order.shipping_code or ''}</shippingCode>
    <weightTotal>{order.weight_total:.3f}</weightTotal>
  </header>
  <customer>
    <name>{(partner.name or '').replace('&','&amp;')}</name>
    <street>{(partner.street or '').replace('&','&amp;')}</street>
    <zip>{partner.zip or ''}</zip>
    <city>{(partner.city or '').replace('&','&amp;')}</city>
    <country>{(partner.country_id and partner.country_id.code) or ''}</country>
    <email>{partner.email or ''}</email>
    <phone>{partner.phone or ''}</phone>
  </customer>
  <lines>{ln_xml}
  </lines>
</deliveryOrder>"""
        return xml