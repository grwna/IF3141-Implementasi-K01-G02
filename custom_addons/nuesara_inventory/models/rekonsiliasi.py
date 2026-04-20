# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RekonsiliasiKeuangan(models.Model):
    _name = 'rekonsiliasi.keuangan'
    _description = 'Rekonsiliasi Keuangan vs Stok'

    bahan_id = fields.Many2one('bahan.baku', string="Bahan", required=True)
    pemakaian_aktual = fields.Float(string="Pemakaian Aktual")
    penjualan_pos = fields.Float(string="Penjualan POS")
    selisih = fields.Float(string="Selisih", compute="_compute_selisih", store=True)
    status = fields.Selection([
        ('match', 'Match'),
        ('mismatch', 'Mismatch'),
    ], string="Status", compute="_compute_status", store=True)

    @api.depends('pemakaian_aktual', 'penjualan_pos')
    def _compute_selisih(self):
        for record in self:
            record.selisih = record.pemakaian_aktual - record.penjualan_pos

    @api.depends('selisih')
    def _compute_status(self):
        for record in self:
            if record.selisih == 0:
                record.status = 'match'
            else:
                record.status = 'mismatch'
