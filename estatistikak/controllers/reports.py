# -*- coding: utf-8 -*-
import csv
import io
from collections import Counter

from odoo import http
from odoo.http import request

from ..models.mysql_client import EskaerakMySQLClient


class EstatistikakReports(http.Controller):

    @http.route('/estatistikak/report/orokorrak.csv', type='http', auth='user')
    def orokorrak_csv(self, **kw):
        values = request.env['estatistikak.estatistika_orokorrak']._get_estatistikak_values()
        rows = [
            ['Metrika', 'Balioa'],
            ['Eskariak guztira', values['total_eskariak']],
            ['Zenbatekoa guztira', values['total_zenbatekoa']],
            ['Batez besteko zenbatekoa', values['batez_besteko_zenbatekoa']],
            ['Mahai kopurua', values['bezero_kopurua']],
            ['Produktuak guztira', values['produktu_kopurua']],
            ['Platerak guztira', values['plater_kopurua']],
        ]
        return self._csv_response('estatistika_orokorrak.csv', rows)

    @http.route('/estatistikak/report/espezifikoak.csv', type='http', auth='user')
    def espezifikoak_csv(self, **kw):
        eskariak = EskaerakMySQLClient(request.env).get_eskaerak_with_totals()
        counts = Counter(self._mysql_date_parts(eskari.get('data')) for eskari in eskariak)
        counts.pop((0, 0, 0), None)
        rows = [['Urtea', 'Hilabetea', 'Hilabeteko eguna', 'Eskari kopurua']]
        rows.extend([year, month, day, counts[(year, month, day)]] for year, month, day in sorted(counts))
        return self._csv_response('estatistika_espezifikoak.csv', rows)

    def _csv_response(self, filename, rows):
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerows(rows)
        content = output.getvalue()
        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ],
        )

    def _mysql_day(self, value):
        if not value:
            return 0
        if hasattr(value, 'day'):
            return value.day
        try:
            return int(str(value).split('T', 1)[0].split(' ', 1)[0].split('-')[-1])
        except (TypeError, ValueError):
            return 0

    def _mysql_date_parts(self, value):
        if not value:
            return (0, 0, 0)
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return (value.year, value.month, value.day)
        try:
            date_part = str(value).split('T', 1)[0].split(' ', 1)[0]
            year, month, day = date_part.split('-')
            return (int(year), int(month), int(day))
        except (TypeError, ValueError):
            return (0, 0, 0)
