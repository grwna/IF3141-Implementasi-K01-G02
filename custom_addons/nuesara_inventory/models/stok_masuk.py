# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StokMasuk(models.Model):
    _name = 'stok.masuk'
    _description = 'Pencatatan Stok Masuk'
    _order = 'tanggal_terima desc'

    tanggal_terima = fields.Date(string="Tanggal Terima", default=fields.Date.today, required=True)
    supplier_id = fields.Many2one('res.partner', string="Supplier", domain=[('is_company', '=', True)])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string="Status", default='draft', required=True)
    line_ids = fields.One2many('stok.masuk.line', 'stok_masuk_id', string="Lines")

    def action_post(self):
        for record in self:
            if record.state == 'draft':
                # TODO: loop through lines and update balances.
                record.state = 'posted'

class StokMasukLine(models.Model):
    _name = 'stok.masuk.line'
    _description = 'Line Item Stok Masuk'

    stok_masuk_id = fields.Many2one('stok.masuk', string="Reference")
    bahan_id = fields.Many2one('bahan.baku', string="Bahan", required=True)
    jumlah_terima = fields.Float(string="Jumlah Terima", required=True)
    satuan = fields.Selection([
        ('gr', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Mililiter'),
        ('l', 'Liter'),
        ('pcs', 'Pcs'),
    ], related='bahan_id.satuan', string="Satuan", readonly=True)
