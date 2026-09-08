from odoo import models, fields

class Partner(models.Model):
    _inherit = 'res.partner'

    member_date = fields.Date(string='Member Since')