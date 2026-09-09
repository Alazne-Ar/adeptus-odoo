from odoo import models, fields

class Booking(models.Model):
    _name = 'adeptus_calvastres.booking'
    _description = 'Booking tables'

    name = fields.Char(string='Name', required=True)
    hour = fields.Float(string='Hour', required=True, help='The hour of the booking')
    table_id = fields.Many2one('adeptus_calvastres.table', string='Table', required=True, help='The table that is booked')