# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import hashlib

class PostnlOrder(models.Model):
    _name = "postnl.order"
    _description = "PostNL Staged Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Name", default=lambda self: self._default_name(), tracking=True)
    sale_id = fields.Many2one("sale.order", string="Sales Order", index=True, tracking=True, ondelete="set null")
    partner_id = fields.Many2one("res.partner", string="Customer", related="sale_id.partner_id", store=True, readonly=True)
    country_id = fields.Many2one("res.country", string="Ship To Country", compute="_compute_country_weight", store=True, readonly=True)
    weight_total = fields.Float(string="Total Weight (kg)", compute="_compute_country_weight", store=True, readonly=True, digits=(12, 3))
    shipping_rule_id = fields.Many2one("postnl.shipping.rule", string="Matched Rule", tracking=True, ondelete="set null")
    shipping_code = fields.Char(string="PostNL Code", tracking=True, help="Chosen shipping/agent code sent to PostNL")
    tracking_number = fields.Char(string="Track & Trace")
    tnt_url = fields.Char(string="Track & Trace URL", compute="_compute_tnt_url", store=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("queued", "Queued"),
        ("exported", "Exported"),
        ("shipped", "Shipped"),
        ("error", "Error"),
    ], default="draft", tracking=True, index=True)

    source = fields.Char(string="Source", default="woocommerce", help="Where this order came from (for reference).")
    last_sync_at = fields.Datetime(string="Last Sync")
    last_error_text = fields.Text(string="Last Error")
    last_error_hash = fields.Char(string="Last Error Hash", copy=False)

    # Derived from sale order (addresses & weights)
    @api.depends("sale_id.partner_shipping_id", "sale_id.order_line.product_id", "sale_id.order_line.product_uom_qty")
    def _compute_country_weight(self):
        for rec in self:
            country = rec.sale_id.partner_shipping_id.country_id if rec.sale_id else False
            weight = 0.0
            if rec.sale_id:
                for line in rec.sale_id.order_line.filtered(lambda l: not l.display_type and l.product_id):
                    w = (line.product_id.weight or 0.0) * (line.product_uom_qty or 0.0)
                    weight += w
            rec.country_id = country.id if country else False
            rec.weight_total = weight

    @api.depends("tracking_number")
    def _compute_tnt_url(self):
        ICP = self.env["ir.config_parameter"].sudo()
        template = ICP.get_param("postnl.tnt_url_template", default="https://tracking.postnl.nl/#!/track/{}")
        for rec in self:
            rec.tnt_url = (template.format(rec.tracking_number) if (rec.tracking_number and "{}" in template) else template)

    @api.model
    def _default_name(self):
        return self.env["ir.sequence"].next_by_code("postnl.order") or _("PostNL Order")

    def _post_single_error(self, text):
        """Post a single chatter message per unique error text (hash) per record."""
        self.ensure_one()
        text = text or _("Unknown error")
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if h != (self.last_error_hash or ""):
            self.message_post(body=_("PostNL error: %s") % text)
            self.write({"last_error_hash": h, "last_error_text": text, "state": "error"})
        # no re-posting if same error hash

    def action_apply_rule(self):
        for rec in self:
            rec._apply_shipping_rule()

    def _apply_shipping_rule(self):
        """Pick best matching shipping rule; else default from config parameter."""
        self.ensure_one()
        Rule = self.env["postnl.shipping.rule"]
        rule = Rule._match(country=self.country_id, weight=self.weight_total)
        if rule:
            self.write({"shipping_rule_id": rule.id, "shipping_code": rule.shipping_code})
            return
        default_code = self.env["ir.config_parameter"].sudo().get_param("postnl.default_shipping_code", default="3085")
        self.write({"shipping_rule_id": False, "shipping_code": default_code})

    def action_queue_export(self):
        for rec in self:
            if not rec.sale_id:
                raise UserError(_("Please link a Sales Order first."))
            if not rec.shipping_code:
                rec._apply_shipping_rule()
            rec.write({"state": "queued"})
        return True

    def action_mark_exported(self):
        self.write({"state": "exported", "last_sync_at": fields.Datetime.now()})
        return True

    def action_mark_shipped(self):
        self.write({"state": "shipped", "last_sync_at": fields.Datetime.now()})
        return True

    def action_open_tnt(self):
        self.ensure_one()
        if not self.tnt_url:
            raise UserError(_("No tracking URL."))
        return {
            "type": "ir.actions.act_url",
            "url": self.tnt_url,
            "target": "new",
        }

    # ---------- CRONS ----------
    @api.model
    def _cron_scan_sale_orders(self):
        """Create staged PostNL orders for confirmed Sales Orders that are not yet staged."""
        Sale = self.env["sale.order"]
        domain = [("state", "in", ["sale", "done"]), ("picking_policy", "!=", False)]
        sales = Sale.search(domain, limit=200)
        created = 0
        for so in sales:
            exists = self.search_count([("sale_id", "=", so.id)])
            if exists:
                continue
            rec = self.create({
                "name": so.name,
                "sale_id": so.id,
            })
            rec._apply_shipping_rule()
            created += 1
        return created

    @api.model
    def _cron_export_orders(self):
        service = self.env["postnl.service"]
        orders = self.search([("state", "=", "queued")], order="id asc", limit=50)
        if not orders:
            return 0
        return service._export_orders_to_postnl(orders)

    @api.model
    def _cron_import_shipments(self):
        service = self.env["postnl.service"]
        return service._import_shipments_update_orders()