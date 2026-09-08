from odoo import models, fields

class Table(models.Model):
    _name = 'adeptus_calvastres.table'
    _description = 'Table'

    name = fields.Char(string='Name', required=True)
    empty_table = fields.Boolean(string='Empty Table', default=True, help='Indicates if the table is empty or not')