from odoo import models, fields, api

class Partner(models.Model):
    _name = 'adeptus_calvastres.partner'
    _description = 'Partner'
    _inherit = ['adeptus_calvastres.notify']

    name = fields.Char(string='Name', required=True)
    surname = fields.Char(string='Surname')
    email = fields.Char(string='Email', required=True)
    mobile = fields.Char(string='Mobile', required=True)
    member_date = fields.Date(string='Member Since')
    is_member = fields.Boolean(string="Is Member", default=False)
    bookings = fields.One2many('adeptus_calvastres.booking', 'partner_id', 
                               string="Bookings", 
                               help="The bookings made by the partner")
    res_partner = fields.Many2one('res.partner', string='Billing Partner', copy=False)


    @api.model_create_multi
    def create(self, vals_list):
        members = super().create(vals_list)
        for member in members:
            if not member.res_partner_id:
                member.res_partner_id = self.env['res.partner'].create({
                    'name': member.name,
                })
            return members