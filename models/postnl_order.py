from odoo import api, fields, models, _
from odoo.exceptions import UserError
import hashlib
import logging

_logger = logging.getLogger(__name__)

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

    @api.depends("sale_id.partner_shipping_id", "sale_id.order_line.product_id", "sale_id.order_line.product_uom_qty")
    def _compute_country_weight(self):
        for rec in self:
            country = rec.sale_id.partner_shipping_id.country_id if rec.sale_id else False
            weight = 0.0
            if rec.sale_id:
                for line in rec.sale_id.order_line.filtered(lambda l: not l.display_type and l.product_id):
                    weight += (line.product_id.weight or 0.0) * (line.product_uom_qty or 0.0)
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
        seq = self.env["ir.sequence"].next_by_code("postnl.order")
        return seq or _("PostNL Order")

    # -------- logging helper ----------
    def _log(self, level, msg, **kw):
        payload = {"order": self.name or self.id, **kw}
        if level == "debug": _logger.debug(msg, payload)
        elif level == "warning": _logger.warning(msg, payload)
        elif level == "error": _logger.error(msg, payload)
        else: _logger.info(msg, payload)

    def _post_single_error(self, text):
        """Post only once per error hash to chatter (but ALWAYS log)."""
        self.ensure_one()
        text = text or _("Unknown error")
        self._log("error", "PostNL error: %s", error=text)
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if h != (self.last_error_hash or ""):
            self.message_post(body=_("PostNL error: %s") % text)
            self.write({"last_error_hash": h, "last_error_text": text, "state": "error"})

    def action_apply_rule(self):
        for rec in self:
            rec._apply_shipping_rule()

    def _apply_shipping_rule(self):
        self.ensure_one()
        self._log("debug", "Apply shipping rule start", weight=self.weight_total, country=self.country_id.code if self.country_id else None)

        # Priority: explicit rules → delivery options mapping → default
        Rule = self.env["postnl.shipping.rule"]
        rule = Rule._match(country=self.country_id, weight=self.weight_total)
        if rule:
            self.write({"shipping_rule_id": rule.id, "shipping_code": rule.shipping_code})
            self._log("info", "Matched shipping rule", rule=rule.name, code=rule.shipping_code)
            return

        # Delivery options influence (from sale.order fields)
        code = self.sale_id._postnl_pick_shipping_code_fallback(self.country_id)
        self.write({"shipping_rule_id": False, "shipping_code": code})
        self._log("info", "Applied delivery-options fallback code", code=code)

    def action_queue_export(self):
        for rec in self:
            if not rec.sale_id:
                raise UserError(_("Please link a Sales Order first."))
            if not rec.shipping_code:
                rec._apply_shipping_rule()
            rec._log("info", "Queued for export")
            rec.write({"state": "queued"})
        return True

    def action_mark_exported(self):
        self._log("info", "Marked as exported")
        self.write({"state": "exported", "last_sync_at": fields.Datetime.now()})
        return True

    def action_mark_shipped(self):
        self._log("info", "Marked as shipped")
        self.write({"state": "shipped", "last_sync_at": fields.Datetime.now()})
        # Optional: auto-complete order if paid, etc. (left conservative)
        return True

    def action_open_tnt(self):
        self.ensure_one()
        if not self.tnt_url:
            raise UserError(_("No tracking URL."))
        self._log("info", "Open Track & Trace", url=self.tnt_url)
        return {"type": "ir.actions.act_url", "url": self.tnt_url, "target": "new"}

    # ---------- CRONS ----------
    @api.model
    def _cron_scan_sale_orders(self):
        Sale = self.env["sale.order"]
        sales = Sale.search([("state", "in", ["sale", "done"])], limit=200)
        created = 0
        for so in sales:
            if self.search_count([("sale_id", "=", so.id)]):
                continue
            rec = self.create({"name": so.name, "sale_id": so.id})
            rec._apply_shipping_rule()
            rec._log("info", "Staged from sale.order", sale=so.name)
            created += 1
        _logger.info("PostNL SCAN: created %s staged orders", created)
        return created

    @api.model
    def _cron_export_orders(self):
        orders = self.search([("state", "=", "queued")], order="id asc", limit=50)
        _logger.info("PostNL EXPORT: %s orders queued", len(orders))
        if not orders:
            return 0
        return self.env["postnl.service"]._export_orders_to_postnl(orders)

    @api.model
    def _cron_import_shipments(self):
        _logger.info("PostNL IMPORT shipments: start")
        return self.env["postnl.service"]._import_shipments_update_orders()
