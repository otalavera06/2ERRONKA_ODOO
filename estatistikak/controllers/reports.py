# -*- coding: utf-8 -*-
import calendar
import io
from collections import Counter

from odoo import fields, http
from odoo.exceptions import UserError
from odoo.http import request

from ..models.mysql_client import EskaerakMySQLClient


class EstatistikakReports(http.Controller):

    MONTH_NAMES = [
        'Urtarrila', 'Otsaila', 'Martxoa', 'Apirila', 'Maiatza', 'Ekaina',
        'Uztaila', 'Abuztua', 'Iraila', 'Urria', 'Azaroa', 'Abendua',
    ]

    @http.route('/estatistikak/report/orokorrak.pdf', type='http', auth='user')
    def orokorrak_pdf(self, **kw):
        eskariak = EskaerakMySQLClient(request.env).get_eskaerak_with_totals()
        values = request.env['estatistikak.estatistika_orokorrak']._get_estatistikak_values()

        type_data = [
            ('Produktuak', values['produktu_kopurua']),
            ('Platerak', values['plater_kopurua']),
        ]
        table_counts = Counter(
            'Mahaia %s' % eskari.get('mahaiak_id')
            for eskari in eskariak
            if eskari.get('mahaiak_id')
        )
        table_data = sorted(table_counts.items(), key=lambda item: item[0])

        metrics = [
            ('Eskariak guztira', values['total_eskariak']),
            ('Zenbatekoa guztira', '%.2f' % values['total_zenbatekoa']),
            ('Batez besteko zenbatekoa', '%.2f' % values['batez_besteko_zenbatekoa']),
            ('Mahai kopurua', values['bezero_kopurua']),
            ('Produktuak guztira', values['produktu_kopurua']),
            ('Platerak guztira', values['plater_kopurua']),
        ]
        total_items = values['produktu_kopurua'] + values['plater_kopurua']
        if total_items:
            metrics.append(('Produktuak %', '%.1f%%' % (values['produktu_kopurua'] * 100.0 / total_items)))
            metrics.append(('Platerak %', '%.1f%%' % (values['plater_kopurua'] * 100.0 / total_items)))
        if table_data:
            top_table = max(table_data, key=lambda item: item[1])
            metrics.append(('Mahai aktiboena', '%s (%s eskari)' % top_table))

        return self._pdf_response(
            'estatistika_orokorrak.pdf',
            'Estatistika Orokorrak',
            metrics,
            [
                ('Produktuak eta Platerak', type_data),
                ('Mahai bakoitzeko eskariak', table_data),
            ],
        )

    @http.route('/estatistikak/report/espezifikoak.pdf', type='http', auth='user')
    def espezifikoak_pdf(self, **kw):
        today = fields.Date.today()
        eskariak = EskaerakMySQLClient(request.env).get_eskaerak_with_totals()
        month_counts = Counter()
        day_counts = Counter()

        for eskari in eskariak:
            parts = self._mysql_date_parts(eskari.get('data'))
            if not parts:
                continue
            year, month, day = parts
            if year == today.year:
                month_counts[month] += 1
                if month == today.month:
                    day_counts[day] += 1

        month_data = [(self.MONTH_NAMES[month - 1], month_counts[month]) for month in range(1, 13)]
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        day_data = [('%s' % day, day_counts[day]) for day in range(1, days_in_month + 1)]

        busiest_month = max(month_data, key=lambda item: item[1]) if month_data else ('-', 0)
        busiest_day = max(day_data, key=lambda item: item[1]) if day_data else ('-', 0)
        metrics = [
            ('Urtea', today.year),
            ('Hilabetea', self.MONTH_NAMES[today.month - 1]),
            ('Urteko eskariak guztira', sum(month_counts.values())),
            ('Hilabeteko eskariak guztira', sum(day_counts.values())),
            ('Hilabete aktiboena', '%s (%s eskari)' % busiest_month),
            ('Egun aktiboena hilabete honetan', '%s (%s eskari)' % busiest_day),
        ]

        return self._pdf_response(
            'estatistika_espezifikoak.pdf',
            'Estatistika Espezifikoak',
            metrics,
            [
                ('Urteko Hilabeteak', month_data),
                ('Hilabeteko Egunak - %s' % self.MONTH_NAMES[today.month - 1], day_data),
            ],
        )

    def _pdf_response(self, filename, title, metrics, charts):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise UserError("PDFak sortzeko `reportlab` falta da Odoo ingurunean: %s" % exc)

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 42
        y = height - margin

        pdf.setTitle(title)
        pdf.setFont('Helvetica-Bold', 18)
        pdf.drawString(margin, y, title)
        y -= 28

        pdf.setFont('Helvetica', 9)
        pdf.setFillColor(colors.HexColor('#555555'))
        pdf.drawString(margin, y, 'Odoo estatistiken txostena')
        pdf.setFillColor(colors.black)
        y -= 28

        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(margin, y, 'Datu nagusiak')
        y -= 18
        pdf.setFont('Helvetica', 10)
        for label, value in metrics:
            pdf.drawString(margin, y, '%s: %s' % (label, value))
            y -= 14
            if y < 90:
                pdf.showPage()
                y = height - margin

        y -= 12
        palette = [
            colors.HexColor('#4E79A7'), colors.HexColor('#F28E2B'),
            colors.HexColor('#59A14F'), colors.HexColor('#E15759'),
            colors.HexColor('#76B7B2'), colors.HexColor('#EDC948'),
            colors.HexColor('#B07AA1'), colors.HexColor('#FF9DA7'),
        ]
        for chart_title, data in charts:
            if y < 270:
                pdf.showPage()
                y = height - margin
            y = self._draw_bar_chart(pdf, chart_title, data, margin, y, width - (margin * 2), 190, palette)
            y -= 24

        pdf.save()
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ],
        )

    def _draw_bar_chart(self, pdf, title, data, x, y, width, height, palette):
        from reportlab.lib import colors

        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(x, y, title)
        chart_top = y - 20
        chart_bottom = chart_top - height
        label_space = 64
        bar_area_width = width - label_space
        max_value = max([value for label, value in data] or [0])
        max_value = max(max_value, 1)

        pdf.setStrokeColor(colors.HexColor('#444444'))
        pdf.line(x + label_space, chart_bottom, x + label_space, chart_top)
        pdf.line(x + label_space, chart_bottom, x + width, chart_bottom)

        pdf.setFont('Helvetica', 8)
        pdf.drawRightString(x + label_space - 6, chart_top - 4, str(max_value))
        pdf.drawRightString(x + label_space - 6, chart_bottom, '0')

        if not data:
            pdf.drawString(x + label_space + 10, chart_bottom + 80, 'Ez dago daturik.')
            return chart_bottom - 18

        gap = 4
        bar_width = max(6, (bar_area_width - (gap * (len(data) + 1))) / float(len(data)))
        for index, (label, value) in enumerate(data):
            bar_height = 0 if not value else (value / float(max_value)) * (height - 20)
            bar_x = x + label_space + gap + index * (bar_width + gap)
            bar_y = chart_bottom
            pdf.setFillColor(palette[index % len(palette)])
            pdf.rect(bar_x, bar_y, bar_width, bar_height, stroke=0, fill=1)
            pdf.setFillColor(colors.black)
            pdf.drawCentredString(bar_x + (bar_width / 2.0), bar_y + bar_height + 3, str(value))

            short_label = label if len(label) <= 10 else label[:9] + '.'
            pdf.saveState()
            pdf.translate(bar_x + (bar_width / 2.0), chart_bottom - 6)
            pdf.rotate(45 if len(data) > 12 else 0)
            pdf.drawCentredString(0, -8 if len(data) > 12 else 0, short_label)
            pdf.restoreState()

        pdf.setFont('Helvetica', 9)
        pdf.drawString(x + label_space, chart_bottom - 44, 'Behean: kategoriak. Ezkerrean: eskari kopurua.')
        return chart_bottom - 58

    def _mysql_date_parts(self, value):
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
