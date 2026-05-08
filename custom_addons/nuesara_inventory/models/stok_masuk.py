# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class StokMasuk(models.Model):
    _name = 'stok.masuk'
    _description = 'Pencatatan Stok Masuk'
    _order = 'tanggal_terima desc'

    tanggal_terima = fields.Date(string="Tanggal Terima", default=fields.Date.today, required=True)
    supplier_id = fields.Many2one(
        'res.partner',
        string="Supplier",
        domain=[('is_company', '=', True)],
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string="Status", default='draft', required=True)
    line_ids = fields.One2many('stok.masuk.line', 'stok_masuk_id', string="Lines")

    @api.constrains('supplier_id')
    def _check_registered_supplier(self):
        for record in self:
            if record.supplier_id and not record.supplier_id.is_company:
                raise ValidationError("Supplier harus dipilih dari daftar perusahaan terdaftar.")

    def action_post(self):
        for record in self:
            if record.state != 'draft':
                continue
            if not record.supplier_id:
                raise ValidationError("Supplier wajib diisi dari daftar supplier terdaftar.")
            if not record.supplier_id.is_company:
                raise ValidationError("Supplier tidak ditemukan dalam daftar perusahaan terdaftar.")
            if not record.line_ids:
                raise ValidationError("Minimal satu bahan baku harus dicatat.")

            low_stock_bahan = self.env['bahan.baku']
            latest_stock_lines = []
            for line in record.line_ids:
                if line.jumlah_terima <= 0:
                    raise ValidationError("Jumlah terima untuk %s harus lebih dari 0." % line.bahan_id.display_name)

            for line in record.line_ids:
                line.bahan_id.with_context(skip_nuesara_log=True).write({
                    'saldo_stok': line.bahan_id.saldo_stok + line.jumlah_terima,
                })
                latest_stock_lines.append(
                    "%s: %.2f %s"
                    % (line.bahan_id.display_name, line.bahan_id.saldo_stok, line.bahan_id.satuan)
                )
                if line.bahan_id.status_stok in ('menipis', 'habis'):
                    low_stock_bahan |= line.bahan_id

            record.state = 'posted'
            self.env['nuesara.activity.log'].sudo().log_action(
                action='post',
                model_name=record._description,
                record_name=record.display_name,
                note="Stok masuk berhasil dicatat dari supplier %s." % record.supplier_id.display_name,
            )

            message = "Stok masuk berhasil dicatat. Saldo terbaru: %s." % "; ".join(latest_stock_lines)
            notification_type = 'success'
            sticky = False
            if low_stock_bahan:
                low_stock_details = [
                    "%s saldo %.2f %s, threshold %.2f %s"
                    % (
                        bahan.display_name,
                        bahan.saldo_stok,
                        bahan.satuan,
                        bahan.nilai_minimum,
                        bahan.satuan,
                    )
                    for bahan in low_stock_bahan
                ]
                message += " Stok masih menipis/habis: %s." % "; ".join(low_stock_details)
                notification_type = 'warning'
                sticky = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Pencatatan Stok Masuk',
                    'message': message,
                    'type': notification_type,
                    'sticky': sticky,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                },
            }
        return True

class StokMasukLine(models.Model):
    _name = 'stok.masuk.line'
    _description = 'Line Item Stok Masuk'

    stok_masuk_id = fields.Many2one('stok.masuk', string="Reference")
    bahan_id = fields.Many2one('bahan.baku', string="Bahan", required=True)
    jumlah_terima = fields.Float(string="Jumlah Terima", required=True)
    satuan = fields.Selection(related='bahan_id.satuan', string="Satuan", readonly=True)

    @api.constrains('jumlah_terima')
    def _check_positive_quantity(self):
        for record in self:
            if record.jumlah_terima <= 0:
                raise ValidationError("Jumlah terima harus lebih dari 0.")
