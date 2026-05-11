# -*- coding: utf-8 -*-
import json

from odoo import api, http, fields, registry, SUPERUSER_ID
from odoo.http import request

class DeskontuakAPI(http.Controller):

    @http.route('/api/check_discount', type='http', auth='none', methods=['POST'], csrf=False)
    def check_discount(self, **post):
        payload = request.httprequest.get_json(silent=True) or {}
        params = payload.get('params') if isinstance(payload.get('params'), dict) else payload
        code = params.get('code')
        if not code:
            return self._json_response({'status': 'error', 'message': 'Kodea falta da'})

        db_name = params.get('db') or 'entregaodoo'
        with registry(db_name).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            discount = env['estatistikak.deskontuak'].sudo().search([
                ('name', '=', code),
                ('aktibo', '=', True),
                ('hasiera_data', '<=', fields.Date.today()),
                ('amaiera_data', '>=', fields.Date.today())
            ], limit=1)

            if discount:
                return self._json_response({
                    'status': 'success',
                    'code': discount.name,
                    'percentage': discount.balioa
                })
        
        return self._json_response({'status': 'error', 'message': 'Kodea ez da baliozkoa'})

    def _json_response(self, data):
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )
