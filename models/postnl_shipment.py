import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PostNLShipment(models.Model):
    _name = "postnl.shipment"
    _description = "PostNL Shipment"
    _order = "create_date desc"

    name = fields.Char(string="Reference", readonly=True, default=lambda self: _("New"))
    picking_id = fields.Many2one("stock.picking", required=True, ondelete="cascade")
    partner_id = fields.Many2one(related="picking_id.partner_id", store=True)
    barcode = fields.Char(string="Barcode / Tracking No.")
    track_trace_url = fields.Char(string="Track & Trace URL")
    label_pdf = fields.Binary(string="Label (PDF)")
    label_description = fields.Char(string="Label Description")

    package_type = fields.Selection([("package","Package"),("mailbox","Mailbox"),("letter","Unpaid Letter")], default="package")
    only_recipient = fields.Boolean()
    signature = fields.Boolean()
    insured = fields.Boolean()
    insured_amount = fields.Float(default=0.0)
    multi_collo = fields.Integer(string="Number of Parcels", default=1)
    state = fields.Selection([("new","New"),("confirmed","Confirmed"),("cancelled","Cancelled")], default="new")

    def action_download_label(self):
        self.ensure_one()
        if not self.label_pdf:
            raise UserError(_("No label PDF available."))
        return {
            "type": "ir.actions.act_url",
            "url": "/postnl/label/%s" % self.id,
            "target": "self",
        }

    def action_create_label(self):
        for rec in self:
            rec._create_or_fetch_label()

    def _create_or_fetch_label(self):
        client = self.env["postnl.client"].sudo()
        if not client.is_configured():
            raise UserError(_("PostNL is not configured. Fill settings first."))

        res = client.create_label_from_picking(self.picking_id, self)
        self.write({
            "barcode": res.get("barcode"),
            "track_trace_url": res.get("track_trace_url"),
            "label_pdf": base64.b64encode(res.get("label_pdf", b"")) if res.get("label_pdf") else False,
            "state": "confirmed",
        })
        # Push tracking to picking
        if self.picking_id and res.get("barcode"):
            self.picking_id.carrier_tracking_ref = res["barcode"]
            if res.get("label_pdf"):
                attach = self.env["ir.attachment"].create({
                    "name": f"PostNL_Label_{res['barcode']}.pdf",
                    "datas": base64.b64encode(res["label_pdf"]),
                    "res_model": "stock.picking",
                    "res_id": self.picking_id.id,
                    "mimetype": "application/pdf",
                })
        return True
