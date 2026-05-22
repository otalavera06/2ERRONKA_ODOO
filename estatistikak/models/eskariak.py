# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .mysql_client import EskaerakMySQLClient


class eskariak(models.Model):
    _name = 'estatistikak.eskariak'
    _description = 'Eskarien MySQL Cachea'

    MONTH_SELECTION = [
        ('01', 'Urtarrila'),
        ('02', 'Otsaila'),
        ('03', 'Martxoa'),
        ('04', 'Apirila'),
        ('05', 'Maiatza'),
        ('06', 'Ekaina'),
        ('07', 'Uztaila'),
        ('08', 'Abuztua'),
        ('09', 'Iraila'),
        ('10', 'Urria'),
        ('11', 'Azaroa'),
        ('12', 'Abendua'),
    ]
    DAY_SELECTION = [('%02d' % day, '%s' % day) for day in range(1, 32)]

    name = fields.Char(string="Eskari Zenbakia", required=True)
    data = fields.Date(string="Data", default=fields.Date.today, required=True)
    day_of_month = fields.Integer(string="Hilabeteko Eguna", compute="_compute_day_of_month", store=True)
    month_of_year = fields.Integer(string="Urteko Hilabetea", compute="_compute_date_parts", store=True)
    year_of_date = fields.Integer(string="Urtea", compute="_compute_date_parts", store=True)
    month_label = fields.Selection(MONTH_SELECTION, string="Urteko Hilabeteak", compute="_compute_date_labels", store=True)
    day_label = fields.Selection(DAY_SELECTION, string="Hilabeteko Egunak", compute="_compute_date_labels", store=True)
    eskari_kopurua = fields.Integer(string="Eskari Kopurua", default=1)
    bezeroa = fields.Char(string="Mahaia")
    zenbatekoa = fields.Float(string="Zenbatekoa")
    produktu_kopurua = fields.Integer(string="Produktu Kopurua")
    plater_kopurua = fields.Integer(string="Plater Kopurua")

    @api.model
    def refresh_from_mysql(self):
        eskaerak = EskaerakMySQLClient(self.env).get_eskaerak_with_totals()
        self.with_context(skip_mysql_sync=True).search([]).unlink()

        for eskaera in eskaerak:
            eskaera_id = eskaera.get('id')
            mahaia_id = eskaera.get('mahaiak_id')
            self.with_context(skip_mysql_sync=True).create({
                'name': 'Eskaera #%s' % eskaera_id,
                'data': self._mysql_date(eskaera.get('data')),
                'eskari_kopurua': 1,
                'bezeroa': 'Mahaia %s' % mahaia_id if mahaia_id else '',
                'zenbatekoa': self._float_value(eskaera.get('zenbatekoa')),
                'produktu_kopurua': self._int_value(eskaera.get('produktu_kopurua')),
                'plater_kopurua': self._int_value(eskaera.get('plater_kopurua')),
            })

    @api.depends('data')
    def _compute_day_of_month(self):
        for rec in self:
            rec.day_of_month = rec.data.day if rec.data else 0

    @api.depends('data')
    def _compute_date_parts(self):
        for rec in self:
            if rec.data:
                rec.month_of_year = rec.data.month
                rec.year_of_date = rec.data.year
            else:
                rec.month_of_year = 0
                rec.year_of_date = 0

    @api.depends('data')
    def _compute_date_labels(self):
        for rec in self:
            if rec.data:
                rec.month_label = '%02d' % rec.data.month
                rec.day_label = '%02d' % rec.data.day
            else:
                rec.month_label = False
                rec.day_label = False

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

    def _int_value(self, value):
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
