# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .mysql_client import EskaerakMySQLClient

class estatistika_orokorrak(models.TransientModel):
    _name = 'estatistikak.estatistika_orokorrak'
    _description = 'Estatistika Orokorrak'

    name = fields.Char(string="Izena", default="Eskarien Estatistika Orokorrak")
    total_eskariak = fields.Integer(string="Eskariak guztira")
    total_zenbatekoa = fields.Float(string="Zenbatekoa guztira (eskariak)", digits=(16, 2))
    batez_besteko_zenbatekoa = fields.Float(string="Batez besteko zenbatekoa", digits=(16, 2))
    bezero_kopurua = fields.Integer(string="Mahai kopurua")
    produktu_kopurua = fields.Integer(string="Produktuak guztira")
    plater_kopurua = fields.Integer(string="Platerak guztira")

    @api.model
    def action_show_stats(self):
        self.env['estatistikak.eskariak'].refresh_from_mysql()
        record = self.create(self._get_estatistikak_values())
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'estatistikak.estatistika_orokorrak',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_show_product_kind_graph(self):
        self.env['estatistikak.eskariak'].refresh_from_mysql()
        return self._graph_action('estatistikak.orokorrak_product_kind_action_graph', 'Produktuak eta Platerak', 'product_kind')

    def action_show_table_graph(self):
        self.env['estatistikak.eskariak'].refresh_from_mysql()
        return self._graph_action('estatistikak.orokorrak_table_action_graph', 'Mahaiak', 'table')

    def action_show_graph(self):
        return self.action_show_product_kind_graph()

    def _graph_action(self, xml_id, name, period_type):
        self.env['estatistikak.grafiko_datuak'].refresh_general()
        action = self.env.ref(xml_id).read()[0]
        action['domain'] = [('period_type', '=', period_type)]
        action['context'] = {}
        action['name'] = name
        return action

    def action_download_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/estatistikak/report/orokorrak.pdf',
            'target': 'self',
        }

    @api.model
    def _get_estatistikak_values(self):
        eskariak = EskaerakMySQLClient(self.env).get_eskaerak_with_totals()
        total_eskariak = len(eskariak)
        total_zenbatekoa = sum(self._float_value(eskari.get('zenbatekoa')) for eskari in eskariak)
        produktu_kopurua = sum(self._int_value(eskari.get('produktu_kopurua')) for eskari in eskariak)
        plater_kopurua = sum(self._int_value(eskari.get('plater_kopurua')) for eskari in eskariak)
        mahaiak = {
            eskari.get('mahaiak_id')
            for eskari in eskariak
            if eskari.get('mahaiak_id')
        }
        return {
            'total_eskariak': total_eskariak,
            'total_zenbatekoa': total_zenbatekoa,
            'batez_besteko_zenbatekoa': total_zenbatekoa / total_eskariak if total_eskariak else 0.0,
            'bezero_kopurua': len(mahaiak),
            'produktu_kopurua': produktu_kopurua,
            'plater_kopurua': plater_kopurua,
        }

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
