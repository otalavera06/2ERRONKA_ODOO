# -*- coding: utf-8 -*-
from odoo import models, fields, api
from collections import Counter

from .mysql_client import EskaerakMySQLClient

class estatistika_espezifikoak(models.TransientModel):
    _name = 'estatistikak.estatistika_espezifikoak'
    _description = 'Estatistika Espezifikoak'

    name = fields.Char(string="Izena", default="Eskari Gehieneko Eguna")
    egun_ohikoena = fields.Integer(string="Egunik Ohikoena", compute="_compute_espezifikoak")
    eskari_kopurua_egun_horretan = fields.Integer(string="Kopurua", compute="_compute_espezifikoak")
    total_eskariak = fields.Integer(string="Guztira", compute="_compute_espezifikoak")
    produktu_kopurua = fields.Integer(string="Produktuak guztira", compute="_compute_espezifikoak")
    plater_kopurua = fields.Integer(string="Platerak guztira", compute="_compute_espezifikoak")

    @api.model
    def action_show_specific_stats(self):
        self.env['estatistikak.eskariak'].refresh_from_mysql()
        record = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'estatistikak.estatistika_espezifikoak',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_show_graph(self):
        self.env['estatistikak.eskariak'].refresh_from_mysql()
        return self.env.ref('estatistikak.eskariak_action_graph').read()[0]
    def action_show_month_graph(self):
        self.env['estatistikak.eskariak'].refresh_from_mysql()
        action = self._graph_action('estatistikak.eskariak_month_action_graph', 'Urteko Hilabeteak')
        return action

    def action_show_day_graph(self):
        self.env['estatistikak.eskariak'].refresh_from_mysql()
        action = self._graph_action('estatistikak.eskariak_day_action_graph', 'Hilabeteko Egunak')
        return action

    def action_show_graph(self):
        return self.action_show_month_graph()

    def _graph_action(self, xml_id, name):
        today = fields.Date.today()
        self.env['estatistikak.grafiko_datuak'].refresh_year(today.year)
        action = self.env.ref(xml_id).read()[0]
        period_type = 'day' if xml_id.endswith('day_action_graph') else 'month'
        action['domain'] = [('period_type', '=', period_type), ('year_of_date', '=', today.year)]
        action['context'] = {
            'search_default_month_%02d' % today.month: 1,
        } if period_type == 'day' else {}
        action['name'] = '%s - %s' % (name, today.year)
        return action

    def action_download_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/estatistikak/report/espezifikoak.csv',
            'target': 'self',
        }

    def _compute_espezifikoak(self):
        for rec in self:
            eskariak = EskaerakMySQLClient(self.env).get_eskaerak_with_totals()
            rec.total_eskariak = len(eskariak)
            rec.produktu_kopurua = sum(rec._int_value(eskari.get('produktu_kopurua')) for eskari in eskariak)
            rec.plater_kopurua = sum(rec._int_value(eskari.get('plater_kopurua')) for eskari in eskariak)
            
            if eskariak:
                egunak = [rec._mysql_day(eskari.get('data')) for eskari in eskariak]
                egunak = [eguna for eguna in egunak if eguna]
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

    def _mysql_day(self, value):
        if not value:
            return 0
        if hasattr(value, 'day'):
            return value.day
        try:
            return int(str(value).split('T', 1)[0].split(' ', 1)[0].split('-')[-1])
        except (TypeError, ValueError):
            return 0

    def _int_value(self, value):
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
