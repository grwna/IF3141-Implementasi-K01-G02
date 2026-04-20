# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StokKeluar(models.Model):
    _name = 'stok.keluar'
    _description = 'Pencatatan Pemakaian Harian'
    _order = 'tanggal desc'

    tanggal = fields.Date(string="Tanggal", default=fields.Date.today, required=True)
    shift = fields.Selection([
        ('pagi', 'Pagi'),
        ('siang', 'Siang'),
        ('malam', 'Malam'),
    ], string="Shift", required=True)
    line_ids = fields.One2many('stok.keluar.line', 'stok_keluar_id', string="Lines")

    def action_confirm_usage(self):
        # TODO 
        pass

class StokKeluarLine(models.Model):
    _name = 'stok.keluar.line'
    _description = 'Line Item Pemakaian'

    stok_keluar_id = fields.Many2one('stok.keluar', string="Reference")
    bahan_id = fields.Many2one('bahan.baku', string="Bahan", required=True)
    jumlah_pakai = fields.Float(string="Jumlah Pakai", required=True)
    satuan = fields.Selection(related='bahan_id.satuan', string="Satuan", readonly=True)
    tanggal = fields.Date(related='stok_keluar_id.tanggal', string="Tanggal", store=True)
