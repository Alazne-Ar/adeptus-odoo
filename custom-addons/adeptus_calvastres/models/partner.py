from odoo import models, fields, api


class Partner(models.Model):
    _name = "adeptus_calvastres.partner"
    _description = "Partner"
    _inherit = ["adeptus_calvastres.notify"]

    name = fields.Char(string="Name", required=True)
    surname = fields.Char(string="Surname")
    email = fields.Char(string="Email", required=True)
    mobile = fields.Char(string="Mobile", required=True)
    member_date = fields.Date(string="Member Since")
    is_member = fields.Boolean(string="Is Member", default=False)
    bookings = fields.One2many(
        "adeptus_calvastres.booking",
        "partner_id",
        string="Bookings",
        help="The bookings made by the partner",
    )
    res_partner_id = fields.Many2one(
        "res.partner", string="Billing Partner", copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        members = super().create(vals_list)
        for member in members:
            if not member.res_partner_id:
                member.res_partner_id = self.env["res.partner"].create(
                    {
                        "name": member.name,
                    }
                )
            return members

    # Function to generate the monthly receipt of the selected member
    def action_generate_monthly_receipt(self):
        product = self.env.ref("adeptus_calvastres.product_monthly_receipt")
        today = fields.Date.context_today(self)
        for socio in self.filtered(lambda s: s.is_member and s.res_partner_id):
            self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": socio.res_partner_id.id,
                    "invoice_date": today,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "quantity": 1,
                                "price_unit": product.list_price,
                            },
                        )
                    ],
                }
            )
