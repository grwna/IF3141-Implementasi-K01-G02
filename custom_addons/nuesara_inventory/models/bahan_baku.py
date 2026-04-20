# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BahanBaku(models.Model):
    _name = 'bahan.baku'
    _description = 'Master Data Bahan Baku'

    name = fields.Char(string="Nama Bahan", required=True)
    kategori = fields.Selection([
        ('bahan_kering', 'Bahan Kering'),
        ('bahan_basah', 'Bahan Basah'),
        ('cairan', 'Cairan'),
        ('lainnya', 'Lainnya'),
    ], string="Kategori", required=True)
    satuan = fields.Selection([
        ('gr', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Mililiter'),
        ('l', 'Liter'),
        ('pcs', 'Pcs'),
    ], string="Satuan", required=True)
    saldo_stok = fields.Float(string="Saldo Stok", default=0.0)
    nilai_minimum = fields.Float(string="Nilai Minimum", default=0.0)
    estimasi_pemakaian_harian = fields.Float(string="Estimasi Pemakaian Harian", default=0.0)
    
    status_stok = fields.Selection([
        ('aman', 'Aman'),
        ('kritis', 'Kritis'),
    ], string="Status Stok", compute="_compute_status_stok", store=True)

    @api.depends('saldo_stok', 'nilai_minimum')
    def _compute_status_stok(self):
        for record in self:
            if record.saldo_stok <= record.nilai_minimum:
                record.status_stok = 'kritis'
            else:
                record.status_stok = 'aman'
