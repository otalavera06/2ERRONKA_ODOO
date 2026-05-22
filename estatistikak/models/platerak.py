# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .mysql_client import EskaerakMySQLClient


class platerak(models.Model):
    _name = 'estatistikak.platerak'
    _description = 'Plateren Kudeaketa'

    name = fields.Char(string="Izena", required=True)
    mysql_id = fields.Integer(string="MySQL ID", readonly=True, copy=False, index=True)
    mota = fields.Char(string="Mota")
    prezioa = fields.Float(string="Prezioa")
    argazkia = fields.Char(string="Argazkia")

    @api.model
    def action_show_platerak(self):
        self.refresh_from_mysql()
        return self.env.ref('estatistikak.platerak_action').read()[0]

    @api.model
    def refresh_from_mysql(self):
        rows = EskaerakMySQLClient(self.env).get_platerak()
        self.with_context(skip_mysql_sync=True).search([]).unlink()
        for row in rows:
            self.with_context(skip_mysql_sync=True).create({
                'mysql_id': row.get('id'),
                'name': row.get('izena') or '',
                'mota': row.get('mota') or '',
                'prezioa': self._float_value(row.get('prezioa')),
                'argazkia': row.get('argazkia') or '',
            })

    @api.model_create_multi
    def create(self, vals_list):
        client = EskaerakMySQLClient(self.env)
        if self.env.context.get('skip_mysql_sync'):
            return super().create(vals_list)

        prepared_vals = []
        for vals in vals_list:
            data = self._mysql_values(vals)
            vals['mysql_id'] = client.create_platera(data)
            prepared_vals.append(vals)
        return super().create(prepared_vals)

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get('skip_mysql_sync'):
            client = EskaerakMySQLClient(self.env)
            for rec in self:
                if rec.mysql_id:
                    client.update_platera(rec.mysql_id, rec._mysql_values())
        return result

    def unlink(self):
        if not self.env.context.get('skip_mysql_sync'):
            client = EskaerakMySQLClient(self.env)
            for rec in self:
                if rec.mysql_id:
                    client.delete_platera(rec.mysql_id)
        return super().unlink()

    def _mysql_values(self, vals=None):
        vals = vals or {}
        rec = self if len(self) == 1 else False
        return {
            'izena': vals.get('name', rec.name if rec else ''),
            'mota': vals.get('mota', rec.mota if rec else ''),
            'prezioa': vals.get('prezioa', rec.prezioa if rec else 0.0),
            'argazkia': vals.get('argazkia', rec.argazkia if rec else ''),
        }

    def _float_value(self, value):
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0
