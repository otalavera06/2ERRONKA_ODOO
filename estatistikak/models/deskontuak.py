# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class deskontuak(models.Model):
    _name = 'estatistikak.deskontuak'
    _description = 'Deskontuen Kudeaketa'

    name = fields.Char(string="Kodea", required=True)
    balioa = fields.Float(string="Ehunekoa (%)", required=True)
    aktibo = fields.Boolean(string="Aktibo", default=True)
    hasiera_data = fields.Date(string="Hasiera Data", required=True)
    amaiera_data = fields.Date(string="Amaiera Data", required=True)

    @api.constrains('balioa')
    def _balioa_konprobatu(self):
        for rec in self:
            if not (0 <= rec.balioa <= 100):
                raise ValidationError("Ehuneko deskontuak 0 eta 100 artean izan behar du.")

    def deskontua_aplikatu(self, prezioa):
        return prezioa * (1 - self.balioa / 100)
