# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

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
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string="Status", default='draft', required=True)
    line_ids = fields.One2many('stok.keluar.line', 'stok_keluar_id', string="Lines")

    def action_confirm_usage(self):
        for record in self:
            if record.state != 'draft':
                continue
            if not record.line_ids:
                raise ValidationError("Minimal satu bahan baku harus dicatat.")

            usage_by_bahan = {}
            for line in record.line_ids:
                if line.jumlah_pakai <= 0:
                    raise ValidationError("Jumlah pakai untuk %s harus lebih dari 0." % line.bahan_id.display_name)
                bahan_vals = usage_by_bahan.setdefault(line.bahan_id.id, {
                    'bahan': line.bahan_id,
                    'jumlah': 0.0,
                })
                bahan_vals['jumlah'] += line.jumlah_pakai

            for bahan_vals in usage_by_bahan.values():
                bahan = bahan_vals['bahan']
                jumlah = bahan_vals['jumlah']
                if bahan.saldo_stok < jumlah:
                    raise ValidationError(
                        "Saldo %s tidak mencukupi. Saldo saat ini %.2f %s, pemakaian %.2f %s."
                        % (bahan.display_name, bahan.saldo_stok, bahan.satuan, jumlah, bahan.satuan)
                    )

            low_stock_bahan = self.env['bahan.baku']
            latest_stock_lines = []
            for bahan_vals in usage_by_bahan.values():
                bahan = bahan_vals['bahan']
                jumlah = bahan_vals['jumlah']
                bahan.with_context(skip_nuesara_log=True).write({
                    'saldo_stok': bahan.saldo_stok - jumlah,
                })
                latest_stock_lines.append(
                    "%s: %.2f %s" % (bahan.display_name, bahan.saldo_stok, bahan.satuan)
                )
                if bahan.status_stok in ('menipis', 'habis'):
                    low_stock_bahan |= bahan

            record.state = 'confirmed'
            self.env['nuesara.activity.log'].sudo().log_action(
                action='confirm',
                model_name=record._description,
                record_name=record.display_name,
                note="Pemakaian harian berhasil dicatat untuk shift %s." % dict(record._fields['shift'].selection)[record.shift],
            )

            message = "Pemakaian harian berhasil dicatat. Saldo terbaru: %s." % "; ".join(latest_stock_lines)
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
                message += " Stok menipis/habis: %s." % "; ".join(low_stock_details)
                notification_type = 'warning'
                sticky = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Pencatatan Pemakaian Harian',
                    'message': message,
                    'type': notification_type,
                    'sticky': sticky,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                },
            }
        return True

class StokKeluarLine(models.Model):
    _name = 'stok.keluar.line'
    _description = 'Line Item Pemakaian'

    stok_keluar_id = fields.Many2one('stok.keluar', string="Reference")
    bahan_id = fields.Many2one('bahan.baku', string="Bahan", required=True)
    jumlah_pakai = fields.Float(string="Jumlah Pakai", required=True)
    satuan = fields.Selection(related='bahan_id.satuan', string="Satuan", readonly=True)
    tanggal = fields.Date(related='stok_keluar_id.tanggal', string="Tanggal", store=True)

    @api.constrains('jumlah_pakai')
    def _check_positive_quantity(self):
        for record in self:
            if record.jumlah_pakai <= 0:
                raise ValidationError("Jumlah pakai harus lebih dari 0.")
