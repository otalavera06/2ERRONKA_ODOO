# -*- coding: utf-8 -*-
import calendar
from collections import Counter

from odoo import models, fields, api

from .mysql_client import EskaerakMySQLClient


class grafiko_datuak(models.Model):
    _name = 'estatistikak.grafiko_datuak'
    _description = 'Estatistiken Grafiko Datuak'
    _order = 'year_of_date, month_number, day_number'

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

    name = fields.Char(string="Izena", required=True)
    period_type = fields.Selection([
        ('month', 'Urteko Hilabeteak'),
        ('day', 'Hilabeteko Egunak'),
    ], string="Grafiko Mota", required=True)
    year_of_date = fields.Integer(string="Urtea", required=True)
    month_number = fields.Integer(string="Hilabete Zenbakia")
    day_number = fields.Integer(string="Egun Zenbakia")
    month_label = fields.Selection(MONTH_SELECTION, string="Urteko Hilabeteak")
    day_label = fields.Selection(DAY_SELECTION, string="Hilabeteko Egunak")
    eskari_kopurua = fields.Integer(string="Eskari Kopurua")

    @api.model
    def refresh_year(self, year):
        year = int(year)
        eskariak = EskaerakMySQLClient(self.env).get_eskaerak_with_totals()
        month_counts = Counter()
        day_counts = Counter()

        for eskari in eskariak:
            date_parts = self._date_parts(eskari.get('data'))
            if not date_parts:
                continue
            eskari_year, month, day = date_parts
            if eskari_year != year:
                continue
            month_counts[month] += 1
            day_counts[(month, day)] += 1

        self.search([('year_of_date', '=', year)]).unlink()

        for month in range(1, 13):
            self.create({
                'name': '%s %s' % (self._month_name(month), year),
                'period_type': 'month',
                'year_of_date': year,
                'month_number': month,
                'day_number': 0,
                'month_label': '%02d' % month,
                'eskari_kopurua': month_counts[month],
            })

            days_in_month = calendar.monthrange(year, month)[1]
            for day in range(1, days_in_month + 1):
                self.create({
                    'name': '%s %s, %s' % (day, self._month_name(month), year),
                    'period_type': 'day',
                    'year_of_date': year,
                    'month_number': month,
                    'day_number': day,
                    'month_label': '%02d' % month,
                    'day_label': '%02d' % day,
                    'eskari_kopurua': day_counts[(month, day)],
                })

    def _date_parts(self, value):
        if not value:
            return False
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return (value.year, value.month, value.day)
        try:
            date_part = str(value).split('T', 1)[0].split(' ', 1)[0]
            year, month, day = date_part.split('-')
            return (int(year), int(month), int(day))
        except (TypeError, ValueError):
            return False

    def _month_name(self, month):
        return dict(self.MONTH_SELECTION).get('%02d' % month, '')
