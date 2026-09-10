from odoo import models, fields

class Partner(models.Model):
    _name = 'adeptus_calvastres.partner'
    _description = 'Partner'

    name = fields.Char(string='Name', required=True)
    surname = fields.Char(string='Surname')
    email = fields.Char(string='Email', required=True)
    mobile = fields.Char(string='Mobile', required=True)
    member_date = fields.Date(string='Member Since')
    is_member = fields.Boolean(string="Is Member", default=False)
    bookings = fields.One2many('adeptus_calvastres.booking', 'partner_id', 
                               string="Bookings", 
                               help="The bookings made by the partner")