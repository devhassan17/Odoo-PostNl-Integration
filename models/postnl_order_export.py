# postnl_odoo_integration/models/postnl_order_export.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    postnl_shipping_code = fields.Char(
        string="PostNL Shipping Code", readonly=True, copy=False
    )
    postnl_exported = fields.Boolean(
        string="Exported to PostNL", readonly=True, copy=False
    )
    postnl_last_export_date = fields.Datetime(
        string="Last PostNL Export Date", readonly=True, copy=False
    )
    postnl_tracking_ref = fields.Char(
        string="PostNL Tracking Reference", readonly=True, copy=False
    )

    def _compute_total_weight_kg(self):
        """Total weight based on product weights."""
        self.ensure_one()
        total_weight = 0.0
        for line in self.order_line:
            if not line.product_id or line.display_type:
                continue
            total_weight += (line.product_id.weight or 0.0) * line.product_uom_qty
        return total_weight

    def _compute_postnl_shipping_code(self):
        ShippingRule = self.env["postnl.shipping.rule"]
        for order in self:
            country = (
                order.partner_shipping_id.country_id or order.partner_id.country_id
            )
            weight_kg = order._compute_total_weight_kg()
            order.postnl_shipping_code = (
                ShippingRule.get_shipping_code(country, weight_kg) or ""
            )

    def _get_postnl_config(self):
        params = self.env["ir.config_parameter"].sudo()
        enabled = params.get_param("postnl_odoo_integration.enabled", "False") == "True"
        if not enabled:
            raise UserError(_("PostNL Integration is not enabled in settings."))
        return {
            "enabled": enabled,
            "export_auto": params.get_param(
                "postnl_odoo_integration.export_auto", "False"
            )
            == "True",
            "export_trigger_state": params.get_param(
                "postnl_odoo_integration.export_trigger_state", "sale"
            ),
            "sftp_host": params.get_param("postnl_odoo_integration.sftp_host"),
            "sftp_port": int(
                params.get_param("postnl_odoo_integration.sftp_port", 22)
            ),
            "sftp_username": params.get_param(
                "postnl_odoo_integration.sftp_username"
            ),
            "sftp_password": params.get_param(
                "postnl_odoo_integration.sftp_password"
            ),
            "sftp_path_orders": params.get_param(
                "postnl_odoo_integration.sftp_path_orders"
            ),
            "export_filename_pattern": params.get_param(
                "postnl_odoo_integration.export_filename_pattern"
            ),
        }

    def action_postnl_export(self):
        """Manual export to PostNL via SFTP."""
        for order in self:
            order._postnl_export_single()

    def _postnl_export_single(self):
        self.ensure_one()
        config = self._get_postnl_config()
        from ..services.postnl_order_builder import build_order_xml
        from ..services.sftp_client import PostNLSFTPClient

        self._compute_postnl_shipping_code()
        xml_bytes, filename = build_order_xml(self, config["export_filename_pattern"])

        client = PostNLSFTPClient(
            host=config["sftp_host"],
            port=config["sftp_port"],
            username=config["sftp_username"],
            password=config["sftp_password"],
        )
        client.upload_file(config["sftp_path_orders"], filename, xml_bytes)

        self.write(
            {
                "postnl_exported": True,
                "postnl_last_export_date": fields.Datetime.now(),
            }
        )
        _logger.info("Order %s exported to PostNL as %s", self.name, filename)

    def write(self, vals):
        """Auto export when state changes if configured."""
        res = super().write(vals)
        params = self.env["ir.config_parameter"].sudo()
        enabled = params.get_param("postnl_odoo_integration.enabled", "False") == "True"
        export_auto = (
            params.get_param("postnl_odoo_integration.export_auto", "False") == "True"
        )
        trigger_state = params.get_param(
            "postnl_odoo_integration.export_trigger_state", "sale"
        )

        if (
            enabled
            and export_auto
            and "state" in vals
            and vals.get("state") == "sale"
            and trigger_state == "sale"
        ):
            for order in self:
                try:
                    order._postnl_export_single()
                except Exception as e:
                    _logger.exception(
                        "Failed to auto-export order %s to PostNL: %s", order.name, e
                    )
        return res


class StockPicking(models.Model):
    _inherit = "stock.picking"

    postnl_shipment_imported = fields.Boolean(
        string="PostNL Shipment Imported", readonly=True, copy=False
    )
    postnl_last_shipment_update = fields.Datetime(
        string="Last PostNL Shipment Update", readonly=True, copy=False
    )

    def write(self, vals):
        """Auto export on delivery done if trigger is 'done'."""
        res = super().write(vals)
        params = self.env["ir.config_parameter"].sudo()
        enabled = params.get_param("postnl_odoo_integration.enabled", "False") == "True"
        export_auto = (
            params.get_param("postnl_odoo_integration.export_auto", "False") == "True"
        )
        trigger_state = params.get_param(
            "postnl_odoo_integration.export_trigger_state", "sale"
        )

        if (
            enabled
            and export_auto
            and "state" in vals
            and vals.get("state") == "done"
            and trigger_state == "done"
        ):
            for picking in self:
                sale = picking.sale_id
                if sale:
                    try:
                        sale._postnl_export_single()
                    except Exception as e:
                        _logger.exception(
                            "Failed to auto-export order %s from picking %s to PostNL: %s",
                            sale.name,
                            picking.name,
                            e,
                        )
        return res
