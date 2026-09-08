from odoo import models, fields

class Partner(models.Model):
    _inherit = 'res.partner'

    member_date = fields.Date(string='Member Since', help='Date when the partner became a member of the association')