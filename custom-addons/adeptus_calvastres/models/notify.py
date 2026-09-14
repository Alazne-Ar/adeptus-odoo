from odoo import models, fields, api

class Notify(models.AbstractModel):
    _name = 'adeptus_calvastres.notify'
    _description = 'Notify new registers'


    @api.model_create_multi
    # Creates the register
    def create(self, vals_list):
        records = super().create(vals_list)
        records._notify_created()
        return records

    # Notifies that it has been created
    def _notify_created(self):
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': 'Success',
                'message': f'{self._description}: new record created',
                'type': 'success',
                'sticky': False,
            },
        )