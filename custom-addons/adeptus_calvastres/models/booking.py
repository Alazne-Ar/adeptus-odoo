from odoo import models, fields

class Booking(models.Model):
    _name = 'adeptus_calvastres.booking'
    _description = 'Booking tables'

    name = fields.Char(string='Name', required=True)
    table_id = fields.Many2one('adeptus_calvastres.table', string='Table', required=True, help='The table that is booked')