# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .mysql_client import EskaerakMySQLClient


class langileak(models.Model):
    _name = 'estatistikak.langileak'
    _description = 'Langileen Kudeaketa'

    name = fields.Char(string="Izena", required=True)
    mysql_id = fields.Integer(string="MySQL ID", readonly=True, copy=False, index=True)
    abizena = fields.Char(string="Abizena")
    erabiltzailea = fields.Char(string="Erabiltzailea", required=True)
    pasahitza = fields.Char(string="Pasahitza", required=True)
    email = fields.Char(string="Email")
    telefonoa = fields.Char(string="Telefonoa")
    baimena = fields.Boolean(string="Baimena")
    mahaiak_id = fields.Integer(string="Mahaiak ID")
    chat_baimena = fields.Boolean(string="Chat Baimena", default=True)

    @api.model
    def action_show_langileak(self):
        self.refresh_from_mysql()
        return self.env.ref('estatistikak.langileak_action').read()[0]

    @api.model
    def refresh_from_mysql(self):
        rows = EskaerakMySQLClient(self.env).get_langileak()
        self.with_context(skip_mysql_sync=True).search([]).unlink()
        for row in rows:
            self.with_context(skip_mysql_sync=True).create({
                'mysql_id': row.get('id'),
                'name': row.get('izena') or '',
                'abizena': row.get('abizena') or '',
                'erabiltzailea': row.get('erabiltzailea') or '',
                'pasahitza': row.get('pasahitza') or '',
                'email': row.get('email') or '',
                'telefonoa': row.get('telefonoa') or '',
                'baimena': bool(row.get('baimena')),
                'mahaiak_id': row.get('mahaiak_id') or 0,
                'chat_baimena': bool(row.get('chat_baimena')),
            })

    @api.model_create_multi
    def create(self, vals_list):
        client = EskaerakMySQLClient(self.env)
        if self.env.context.get('skip_mysql_sync'):
            return super().create(vals_list)

        prepared_vals = []
        for vals in vals_list:
            data = self._mysql_values(vals)
            vals['mysql_id'] = client.create_langilea(data)
            prepared_vals.append(vals)
        return super().create(prepared_vals)

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get('skip_mysql_sync'):
            client = EskaerakMySQLClient(self.env)
            for rec in self:
                if rec.mysql_id:
                    client.update_langilea(rec.mysql_id, rec._mysql_values())
        return result

    def unlink(self):
        if not self.env.context.get('skip_mysql_sync'):
            client = EskaerakMySQLClient(self.env)
            for rec in self:
                if rec.mysql_id:
                    client.delete_langilea(rec.mysql_id)
        return super().unlink()

    def _mysql_values(self, vals=None):
        vals = vals or {}
        rec = self if len(self) == 1 else False
        return {
            'izena': vals.get('name', rec.name if rec else ''),
            'abizena': vals.get('abizena', rec.abizena if rec else ''),
            'erabiltzailea': vals.get('erabiltzailea', rec.erabiltzailea if rec else ''),
            'pasahitza': vals.get('pasahitza', rec.pasahitza if rec else ''),
            'email': vals.get('email', rec.email if rec else ''),
            'telefonoa': vals.get('telefonoa', rec.telefonoa if rec else ''),
            'baimena': 1 if vals.get('baimena', rec.baimena if rec else False) else 0,
            'mahaiak_id': vals.get('mahaiak_id', rec.mahaiak_id if rec else 0) or None,
            'chat_baimena': 1 if vals.get('chat_baimena', rec.chat_baimena if rec else True) else 0,
        }
