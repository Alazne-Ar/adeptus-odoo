from odoo import models, fields

class Table(models.Model):
    _name = 'adeptus_calvastres.table'
    _description = 'Table'
    _inherit = ['adeptus_calvastres.notify']

    name = fields.Char(string='Name', required=True)
    empty_table = fields.Boolean(string='Empty Table', default=True, help='Indicates if the table is empty or not')
    bookings = fields.One2many('adeptus_calvastres.booking', 'table_id', string="Bookings", help="The bookings for this table")

    # pos_X = fields.Integer(string='Position X (pixels)', required=True, help='The X position of the table')
    # pos_Y = fields.Integer(string='Position Y (pixels)', required=True, help='The Y position of the table')