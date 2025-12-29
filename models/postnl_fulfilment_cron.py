# -*- coding: utf-8 -*-
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)

class PostNLFulfilmentCron(models.Model):
    _name = "postnl.fulfilment.cron"
    _description = "PostNL Fulfilment Cron Processor"

    @api.model
    def run_process_shipment_queue(self, limit=20):
        Queue = self.env["postnl.fulfilment.shipment.queue"].sudo()
        SaleOrder = self.env["sale.order"].sudo()

        jobs = Queue.search([("state", "in", ("new", "failed"))], limit=limit, order="create_date asc")

        for job in jobs:
            try:
                job.state = "processing"
                job.attempts += 1

                payload = job._parse_payload()

                meta = {
                    "merchantCode": payload.get("merchantCode"),
                    "type": payload.get("type"),
                    "messageNo": payload.get("messageNo"),
                    "date": payload.get("date"),
                    "time": payload.get("time"),
                }
                order_status_list = payload.get("orderStatus") or []
                if not isinstance(order_status_list, list):
                    raise ValueError("orderStatus is not a list")

                updated = 0
                for os_item in order_status_list:
                    order_no = os_item.get("orderNo")
                    if not order_no:
                        continue

                    # Matching strategy (adjust if needed)
                    so = SaleOrder.search([
                        "|", "|",
                        ("postnl_fulfilment_order_no", "=", order_no),
                        ("name", "=", order_no),
                        ("client_order_ref", "=", order_no),
                    ], limit=1)

                    if not so:
                        _logger.warning("No Sale Order found for orderNo=%s", order_no)
                        continue

                    so._postnl_apply_shipment(meta, os_item)
                    updated += 1

                job.state = "done"
                job.last_error = False

            except Exception as e:
                _logger.exception("Shipment queue processing failed: %s", e)
                job.state = "failed"
                job.last_error = str(e)
