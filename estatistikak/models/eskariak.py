# -*- coding: utf-8 -*-
from odoo import models, fields, api

class eskariak(models.Model):
    _name = 'estatistikak.eskariak'
    _description = 'Eskariak'

    name = fields.Char(string="Eskari Zenbakia", required=True)
    data = fields.Date(string="Data", default=fields.Date.today, required=True)
    day_of_month = fields.Integer(string="Hilabeteko Eguna", compute="_compute_day_of_month", store=True)
    bezeroa = fields.Char(string="Bezeroa")
    zenbatekoa = fields.Float(string="Zenbatekoa")

    @api.depends('data')
    def _compute_day_of_month(self):
        for rec in self:
            if rec.data:
                rec.day_of_month = rec.data.day
            else:
                rec.day_of_month = 0
