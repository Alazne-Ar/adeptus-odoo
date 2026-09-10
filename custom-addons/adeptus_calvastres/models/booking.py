from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Booking(models.Model):
    _name = 'adeptus_calvastres.booking'
    _description = 'Booking tables'

    name = fields.Char(string='Name', required=True)
    hour = fields.Float(string='Hour', required=True, help='The hour of the booking')
    partner_id = fields.Many2one('adeptus_calvastres.partner', string='Partner', required=True, help='The partner who made the booking')
    table_id = fields.Many2one('adeptus_calvastres.table', string='Table', required=True, help='The table that is booked')
    date = fields.Date(string='Date', required=True, help='The date of the booking')
    state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', help='The status of the booking')


    @api.model_create_multi
    def create(self, vals_list):
        records = super(Booking, self).create(vals_list)
        for record in records:
            if record.table_id.empty_table == False:
                raise ValidationError(('The table is not empty. Please check the table status.'))
            if record.state == 'confirmed':
                record.table_id.empty_table = False
        return records

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
            record.table_id.empty_table = True