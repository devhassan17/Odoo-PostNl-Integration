# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    postnl_sftp_host = fields.Char(string="SFTP Host")
    postnl_sftp_port = fields.Integer(string="SFTP Port", default=22)
    postnl_sftp_user = fields.Char(string="SFTP Username")
    postnl_sftp_password = fields.Char(string="SFTP Password")
    postnl_remote_order_path = fields.Char(string="Remote Order Path", default="/in/orders")
    postnl_remote_shipment_path = fields.Char(string="Remote Shipment Path", default="/out/shipments")
    postnl_remote_stock_path = fields.Char(string="Remote Stock Path", default="/out/stock")
    postnl_batch_size = fields.Integer(string="Order Batch Size", default=50)
    postnl_default_shipping_code = fields.Char(string="Default Shipping Code", default="3085")
    postnl_tnt_url_template = fields.Char(string="Track & Trace URL Template", default="https://tracking.postnl.nl/#!/track/{}")
    postnl_enable_export_cron = fields.Boolean(string="Enable Order Export Cron", default=True)
    postnl_enable_import_cron = fields.Boolean(string="Enable Shipment Import Cron", default=True)
    postnl_enable_scan_cron = fields.Boolean(string="Enable SO Scanner Cron", default=True)

    def set_values(self):
        res = super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        for f in [
            "postnl_sftp_host","postnl_sftp_port","postnl_sftp_user","postnl_sftp_password",
            "postnl_remote_order_path","postnl_remote_shipment_path","postnl_remote_stock_path",
            "postnl_batch_size","postnl_default_shipping_code","postnl_tnt_url_template",
            "postnl_enable_export_cron","postnl_enable_import_cron","postnl_enable_scan_cron",
        ]:
            ICP.set_param(f"postnl.{f[7:]}", getattr(self, f) or "")
        # Toggle crons
        try:
            self.env.ref("postnl_integration.ir_cron_postnl_export").sudo().write({"active": bool(self.postnl_enable_export_cron)})
        except Exception:
            pass
        try:
            self.env.ref("postnl_integration.ir_cron_postnl_import").sudo().write({"active": bool(self.postnl_enable_import_cron)})
        except Exception:
            pass
        try:
            self.env.ref("postnl_integration.ir_cron_postnl_scan").sudo().write({"active": bool(self.postnl_enable_scan_cron)})
        except Exception:
            pass
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        get = lambda k, d="": ICP.get_param(k, default=d)
        res.update(
            postnl_sftp_host=get("postnl.sftp_host"),
            postnl_sftp_port=int(get("postnl.sftp_port", 22) or 22),
            postnl_sftp_user=get("postnl.sftp_user"),
            postnl_sftp_password=get("postnl.sftp_password"),
            postnl_remote_order_path=get("postnl.remote_order_path", "/in/orders"),
            postnl_remote_shipment_path=get("postnl.remote_shipment_path", "/out/shipments"),
            postnl_remote_stock_path=get("postnl.remote_stock_path", "/out/stock"),
            postnl_batch_size=int(get("postnl.batch_size", 50) or 50),
            postnl_default_shipping_code=get("postnl.default_shipping_code", "3085"),
            postnl_tnt_url_template=get("postnl.tnt_url_template", "https://tracking.postnl.nl/#!/track/{}"),
            postnl_enable_export_cron=(get("postnl.enable_export_cron","True") in ("True","1","true")),
            postnl_enable_import_cron=(get("postnl.enable_import_cron","True") in ("True","1","true")),
            postnl_enable_scan_cron=(get("postnl.enable_scan_cron","True") in ("True","1","true")),
        )
        return res