# -*- coding: utf-8 -*-
import json

from odoo import api, http, fields, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.http import request

class DeskontuakAPI(http.Controller):

    @http.route('/api/check_discount', type='http', auth='none', methods=['POST'], csrf=False)
    def check_discount(self, **post):
        try:
            body = request.httprequest.data.decode('utf-8') if request.httprequest.data else '{}'
            payload = json.loads(body) if body else {}
        except (TypeError, ValueError):
            payload = {}

        params = payload.get('params') if isinstance(payload.get('params'), dict) else payload
        code = params.get('code')
        if not code:
            return self._json_response({'status': 'error', 'message': 'Kodea falta da'})

        db_name = params.get('db') or 'entregaodoo'
        with Registry(db_name).cursor() as cr:
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
