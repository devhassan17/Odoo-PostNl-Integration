# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PostNLBaseService(models.AbstractModel):
    _name = "postnl.base.service"
    _description = "PostNL Base Service"

    def __init__(self, env):
        self.env = env

    def get_config(self):
        config = self.env["postnl.config"].search([], limit=1)
        if not config:
            raise Exception("PostNL configuration not found.")
        return config

    def get_replenishment_service(self):
        from .postnl_replenishment import PostNLReplenishmentService
        return PostNLReplenishmentService(self.env)
