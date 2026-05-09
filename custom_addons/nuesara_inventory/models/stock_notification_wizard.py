# -*- coding: utf-8 -*-
from odoo import fields, models


class StockNotificationWizard(models.TransientModel):
    _name = 'nuesara.stock.notification.wizard'
    _description = 'Notifikasi Stok'

    title = fields.Char(string="Judul", readonly=True)
    message = fields.Text(string="Pesan", readonly=True)
