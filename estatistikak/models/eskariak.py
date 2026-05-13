# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .mysql_client import EskaerakMySQLClient

class eskariak(models.Model):
    _name = 'estatistikak.eskariak'
    _description = 'Eskarien MySQL Cachea'

    name = fields.Char(string="Eskari Zenbakia", required=True)
    data = fields.Date(string="Data", default=fields.Date.today, required=True)
    day_of_month = fields.Integer(string="Hilabeteko Eguna", compute="_compute_day_of_month", store=True)
    bezeroa = fields.Char(string="Mahaia")
    zenbatekoa = fields.Float(string="Zenbatekoa")

    @api.model
    def refresh_from_mysql(self):
        eskaerak = EskaerakMySQLClient(self.env).get_eskaerak_with_totals()
        self.search([]).unlink()

        for eskaera in eskaerak:
            eskaera_id = eskaera.get('id')
            mahaia_id = eskaera.get('mahaiak_id')
            self.create({
                'name': 'Eskaera #%s' % eskaera_id,
                'data': self._mysql_date(eskaera.get('data')),
                'bezeroa': 'Mahaia %s' % mahaia_id if mahaia_id else '',
                'zenbatekoa': self._float_value(eskaera.get('zenbatekoa')),
            })

    @api.depends('data')
    def _compute_day_of_month(self):
        for rec in self:
            if rec.data:
                rec.day_of_month = rec.data.day
            else:
                rec.day_of_month = 0

    @api.model
    def _mysql_date(self, value):
        if not value:
            return fields.Date.today()
        if hasattr(value, 'date'):
            return value.date()
        return str(value).split('T', 1)[0].split(' ', 1)[0]

    def _float_value(self, value):
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0
