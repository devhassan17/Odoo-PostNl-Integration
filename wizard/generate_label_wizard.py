from odoo import models, fields, api, _
from odoo.exceptions import UserError

class GeneratePostNLLabelWizard(models.TransientModel):
    _name = "postnl.generate.label.wizard"
    _description = "Generate PostNL Label"

    picking_id = fields.Many2one("stock.picking", required=True)
    label_description = fields.Char()
    package_type = fields.Selection([("package","Package"),("mailbox","Mailbox"),("letter","Unpaid Letter")], default="package")
    only_recipient = fields.Boolean()
    signature = fields.Boolean()
    insured = fields.Boolean()
    insured_amount = fields.Float()
    multi_collo = fields.Integer(default=1)

    def action_generate(self):
        self.ensure_one()
        shipment = self.env["postnl.shipment"].create({
            "picking_id": self.picking_id.id,
            "label_description": self.label_description,
            "package_type": self.package_type,
            "only_recipient": self.only_recipient,
            "signature": self.signature,
            "insured": self.insured,
            "insured_amount": self.insured_amount,
            "multi_collo": self.multi_collo,
        })
        shipment.action_create_label()
        return {
            "type": "ir.actions.act_window",
            "res_model": "postnl.shipment",
            "res_id": shipment.id,
            "view_mode": "form",
            "target": "current"
        }
