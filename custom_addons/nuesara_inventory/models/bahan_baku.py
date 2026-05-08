# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

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
        ('menipis', 'Menipis'),
        ('habis', 'Habis'),
    ], string="Status Stok", compute="_compute_status_stok", store=True)

    @api.depends('saldo_stok', 'nilai_minimum')
    def _compute_status_stok(self):
        for record in self:
            if record.saldo_stok <= 0:
                record.status_stok = 'habis'
            elif record.saldo_stok <= record.nilai_minimum:
                record.status_stok = 'menipis'
            else:
                record.status_stok = 'aman'

    @api.constrains('saldo_stok', 'nilai_minimum', 'estimasi_pemakaian_harian')
    def _check_non_negative_values(self):
        for record in self:
            if record.saldo_stok < 0:
                raise ValidationError("Saldo stok tidak boleh negatif.")
            if record.nilai_minimum <= 0:
                raise ValidationError("Nilai minimum harus lebih dari 0.")
            if record.estimasi_pemakaian_harian < 0:
                raise ValidationError("Estimasi pemakaian harian tidak boleh negatif.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._log_inventory_activity("create", "Data bahan baku berhasil disimpan.")
        return records

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get('skip_nuesara_log'):
            self._log_inventory_activity("write", "Data bahan baku berhasil diperbarui.")
        return result

    def unlink(self):
        self._log_inventory_activity("unlink", "Data bahan baku dihapus.")
        return super().unlink()

    def _log_inventory_activity(self, action, note):
        log_model = self.env['nuesara.activity.log'].sudo()
        for record in self:
            log_model.log_action(
                action=action,
                model_name=self._description,
                record_name=record.display_name,
                note=note,
            )

    def action_open_delete_wizard(self):
        self.ensure_one()
        return {
            'name': 'Konfirmasi Hapus Tahap 2',
            'type': 'ir.actions.act_window',
            'res_model': 'bahan.baku.delete.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bahan_id': self.id},
        }


class BahanBakuDeleteWizard(models.TransientModel):
    _name = 'bahan.baku.delete.wizard'
    _description = 'Konfirmasi Hapus Bahan Baku'

    bahan_id = fields.Many2one('bahan.baku', string="Bahan Baku", required=True, readonly=True)
    confirmation_text = fields.Char(string="Ketik HAPUS")

    def action_confirm_delete(self):
        self.ensure_one()
        if self.confirmation_text != 'HAPUS':
            raise ValidationError("Ketik HAPUS untuk mengonfirmasi penghapusan tahap kedua.")
        self.bahan_id.unlink()
        return {'type': 'ir.actions.act_window_close'}
