# -*- coding: utf-8 -*-
from odoo import api, fields, models


class NuesaraActivityLog(models.Model):
    _name = 'nuesara.activity.log'
    _description = 'Log Aktivitas Nuesara Inventory'
    _order = 'timestamp desc'

    timestamp = fields.Datetime(string="Timestamp", default=fields.Datetime.now, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Pengguna", default=lambda self: self.env.user, readonly=True)
    action = fields.Char(string="Jenis Aktivitas", required=True, readonly=True)
    model_name = fields.Char(string="Modul", readonly=True)
    record_name = fields.Char(string="Record", readonly=True)
    note = fields.Text(string="Keterangan", readonly=True)

    @api.model
    def log_action(self, action, model_name=None, record_name=None, note=None):
        return self.create({
            'action': action,
            'model_name': model_name,
            'record_name': record_name,
            'note': note,
        })
