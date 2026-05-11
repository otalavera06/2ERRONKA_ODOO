# -*- coding: utf-8 -*-
from odoo import models, fields, api
from collections import Counter

class estatistika_espezifikoak(models.TransientModel):
    _name = 'estatistikak.estatistika_espezifikoak'
    _description = 'Estatistika Espezifikoak'

    name = fields.Char(string="Izena", default="Eskari Gehieneko Eguna")
    egun_ohikoena = fields.Integer(string="Egunik Ohikoena", compute="_compute_espezifikoak")
    eskari_kopurua_egun_horretan = fields.Integer(string="Kopurua", compute="_compute_espezifikoak")
    total_eskariak = fields.Integer(string="Guztira", compute="_compute_espezifikoak")

    @api.model
    def action_show_specific_stats(self):
        record = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'estatistikak.estatistika_espezifikoak',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _compute_espezifikoak(self):
        for rec in self:
            eskariak = self.env['estatistikak.eskariak'].search([])
            rec.total_eskariak = len(eskariak)
            
            if eskariak:
                egunak = [eskari.data.day for eskari in eskariak if eskari.data]
                if egunak:
                    ohikoena = Counter(egunak).most_common(1)[0]
                    rec.egun_ohikoena = ohikoena[0]
                    rec.eskari_kopurua_egun_horretan = ohikoena[1]
                else:
                    rec.egun_ohikoena = 0
                    rec.eskari_kopurua_egun_horretan = 0
            else:
                rec.egun_ohikoena = 0
                rec.eskari_kopurua_egun_horretan = 0
