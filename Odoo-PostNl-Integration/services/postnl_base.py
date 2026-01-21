# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PostNLBaseService(models.AbstractModel):
    _name = "postnl.base.service"
    _description = "PostNL Base Service"

    def get_config(self):
        """
        Fetch PostNL configuration (singleton)
        """
        config = self.env["postnl.config"].search([], limit=1)
        if not config:
            raise Exception("PostNL configuration not found.")
        return config

    def get_replenishment_service(self):
        """
        Return replenishment service
        """
        return self.env["postnl.replenishment.service"]
