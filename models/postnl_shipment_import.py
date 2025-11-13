# postnl_odoo_integration/models/postnl_shipment_import.py
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class PostNLShipmentImport(models.Model):
    _name = "postnl.shipment.import"
    _description = "PostNL Shipment Import"

    name = fields.Char(default="PostNL Shipment Import")

    @api.model
    def _get_config(self):
        params = self.env["ir.config_parameter"].sudo()
        return {
            "enabled": params.get_param("postnl_odoo_integration.enabled", "False")
            == "True",
            "import_auto": params.get_param(
                "postnl_odoo_integration.import_auto", "False"
            )
            == "True",
            "import_auto_done": params.get_param(
                "postnl_odoo_integration.import_auto_done", "False"
            )
            == "True",
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
            "sftp_path_shipments": params.get_param(
                "postnl_odoo_integration.sftp_path_shipments"
            ),
        }

    @api.model
    def cron_import_shipments(self):
        config = self._get_config()
        if not (config["enabled"] and config["import_auto"]):
            _logger.info("PostNL shipment import skipped (disabled in settings).")
            return

        from ..services.sftp_client import PostNLSFTPClient
        from ..services.postnl_shipment_parser import parse_shipments

        client = PostNLSFTPClient(
            host=config["sftp_host"],
            port=config["sftp_port"],
            username=config["sftp_username"],
            password=config["sftp_password"],
        )
        directory = config["sftp_path_shipments"] or "."
        filenames = client.list_files(directory)
        _logger.info("PostNL shipment files found: %s", filenames)

        for filename in filenames:
            try:
                content = client.read_file(directory, filename)
                shipments = parse_shipments(content)
                self._apply_shipments(shipments, config)
                # delete file after success
                client.delete_file(directory, filename)
            except Exception as e:
                _logger.exception(
                    "Failed to import PostNL shipment file %s: %s", filename, e
                )

    def _apply_shipments(self, shipments, config):
        """Apply shipment data to pickings and sale orders."""
        for ship in shipments:
            ref = ship.get("order_ref")
            tracking = ship.get("tracking_number")
            status = ship.get("status")
            delivered = ship.get("delivered", False)

            if not ref:
                continue

            sale = self.env["sale.order"].search([("name", "=", ref)], limit=1)
            if not sale:
                _logger.warning("No sale order found for PostNL shipment ref %s", ref)
                continue

            # update tracking on order
            if tracking:
                sale.postnl_tracking_ref = tracking
                # also update related pickings' tracking ref
                for picking in sale.picking_ids:
                    picking.carrier_tracking_ref = tracking

            # mark pickings as imported
            for picking in sale.picking_ids:
                picking.postnl_shipment_imported = True
                picking.postnl_last_shipment_update = fields.Datetime.now()
                if delivered and config.get("import_auto_done") and picking.state not in (
                    "done",
                    "cancel",
                ):
                    try:
                        picking.action_assign()
                        picking.action_confirm()
                        if hasattr(picking, "button_validate"):
                            picking.button_validate()
                    except Exception as e:
                        _logger.exception(
                            "Failed to validate picking %s from PostNL shipment: %s",
                            picking.name,
                            e,
                        )

            _logger.info(
                "Applied PostNL shipment update for order %s, tracking %s, status %s",
                sale.name,
                tracking,
                status,
            )
