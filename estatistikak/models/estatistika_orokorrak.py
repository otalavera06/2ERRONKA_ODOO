# -*- coding: utf-8 -*-
from odoo import models, fields, api

class estatistika_orokorrak(models.TransientModel):
    _name = 'estatistikak.estatistika_orokorrak'
    _description = 'Estatistika Orokorrak'

    name = fields.Char(string="Izena", default="Eskarien Estatistika Orokorrak")
    total_eskariak = fields.Integer(string="Eskariak guztira")
    total_zenbatekoa = fields.Float(string="Zenbatekoa guztira (eskariak)", digits=(16, 2))
    batez_besteko_zenbatekoa = fields.Float(string="Batez besteko zenbatekoa", digits=(16, 2))
    bezero_kopurua = fields.Integer(string="Bezero kopurua")

    @api.model
    def action_show_stats(self):
        record = self.create(self._get_estatistikak_values())
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'estatistikak.estatistika_orokorrak',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _get_estatistikak_values(self):
        eskariak = self.env['estatistikak.eskariak'].search([])
        total_eskariak = len(eskariak)
        total_zenbatekoa = sum(eskariak.mapped('zenbatekoa'))
        return {
            'total_eskariak': total_eskariak,
            'total_zenbatekoa': total_zenbatekoa,
            'batez_besteko_zenbatekoa': total_zenbatekoa / total_eskariak if total_eskariak else 0.0,
            'bezero_kopurua': len(set(eskariak.mapped('bezeroa')) - {False, ''}),
        }
