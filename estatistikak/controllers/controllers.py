# -*- coding: utf-8 -*-
# from odoo import http


# class Estatistikak(http.Controller):
#     @http.route('/estatistikak/estatistikak', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estatistikak/estatistikak/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('estatistikak.listing', {
#             'root': '/estatistikak/estatistikak',
#             'objects': http.request.env['estatistikak.estatistikak'].search([]),
#         })

#     @http.route('/estatistikak/estatistikak/objects/<model("estatistikak.estatistikak"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estatistikak.object', {
#             'object': obj
#         })
