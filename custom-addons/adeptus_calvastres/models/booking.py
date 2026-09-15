from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Booking(models.Model):
    _name = "adeptus_calvastres.booking"
    _description = "Booking tables"
    _inherit = ["adeptus_calvastres.notify"]

    name = fields.Char(string="Name", required=True)
    hour = fields.Float(string="Hour", required=True, help="The hour of the booking")
    partner_id = fields.Many2one(
        "adeptus_calvastres.partner",
        string="Partner",
        required=True,
        help="The partner who made the booking",
    )
    table_id = fields.Many2one(
        "adeptus_calvastres.table",
        string="Table",
        required=True,
        help="The table that is booked",
    )
    shift = fields.Selection(
        [("morning", "Mañana"), ("afternoon", "Tarde"), ("evening", "Noche")],
        string="Turn",
        required=True,
        help="Turn of the day of booking",
    )
    date = fields.Date(string="Date", required=True, help="The date of the booking")
    state = fields.Selection(
        [
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="confirmed",
        help="The status of the booking",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Booking, self).create(vals_list)
        for record in records:
            if record.table_id.empty_table == False:
                raise ValidationError(
                    ("The table is not empty. Please check the table status.")
                )
            if record.state == "confirmed":
                record.table_id.empty_table = False
        return records

    def action_cancel(self):
        for record in self:
            record.state = "cancelled"
            record.table_id.empty_table = True

    @api.constrains("table_id,", "date", "shift", "shift")
    def check_overlap(self):
        for record in self:
            if record.state != "confirmed":
                continue
            overlap = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("table_id", "=", record.table_id.id),
                    ("date", "=", record.date),
                    ("shift", "=", record.shift),
                    ("state", "=", record.state),
                ]
            )
            if overlap:
                raise ValidationError(
                    f"La mesa {record.table_id.name} no está disponible en ese turno"
                )

    @api.constrains("shift", "hour")
    def shift_matches_hour(self):
        range = {
            "morning": (6, 14),
            "afternoon": (14, 20),
            "evening": (20, 24),
        }
        for record in self:
            start, finish = range[record.shift]
            if not (start <= record.hour < finish):
                hours = int(record.hour)
                minutes = int(round((record.hour - hours) * 60))
                advertisement_hour = f"{hours:02d}:{minutes:02d}"
                raise ValidationError(
                    f"La hora {advertisement_hour}, no corresponde al turno seleccionado"
                )
