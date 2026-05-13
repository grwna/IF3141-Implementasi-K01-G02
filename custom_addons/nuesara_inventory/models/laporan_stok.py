# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class LaporanStokHarian(models.Model):
    _name = 'laporan.stok.harian'
    _description = 'Laporan Harian Penggunaan Bahan Baku'
    _auto = False
    _order = 'tanggal desc, bahan_id'

    tanggal = fields.Date(string="Tanggal", readonly=True)
    tanggal_group = fields.Char(string="Tanggal Rekap", readonly=True)
    bulan = fields.Date(string="Bulan", readonly=True)
    bulan_group = fields.Char(string="Bulan Rekap", readonly=True)
    bahan_id = fields.Many2one('bahan.baku', string="Bahan Baku", readonly=True)
    kategori = fields.Selection([
        ('bahan_kering', 'Bahan Kering'),
        ('bahan_basah', 'Bahan Basah'),
        ('cairan', 'Cairan'),
        ('lainnya', 'Lainnya'),
    ], string="Kategori", readonly=True)
    satuan = fields.Selection([
        ('gr', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Mililiter'),
        ('l', 'Liter'),
        ('pcs', 'Pcs'),
    ], string="Satuan", readonly=True)
    total_masuk = fields.Float(string="Total Stok Masuk", readonly=True)
    total_keluar = fields.Float(string="Total Stok Keluar", readonly=True)
    saldo_akhir = fields.Float(string="Saldo Akhir", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW laporan_stok_harian AS (
                WITH tanggal_bahan AS (
                    SELECT sm.tanggal_terima::date AS tanggal, sml.bahan_id
                    FROM stok_masuk_line sml
                    JOIN stok_masuk sm ON sm.id = sml.stok_masuk_id
                    WHERE sm.state = 'posted'
                    UNION
                    SELECT sk.tanggal::date AS tanggal, skl.bahan_id
                    FROM stok_keluar_line skl
                    JOIN stok_keluar sk ON sk.id = skl.stok_keluar_id
                    WHERE sk.state = 'confirmed'
                ),
                masuk AS (
                    SELECT sm.tanggal_terima::date AS tanggal, sml.bahan_id, SUM(sml.jumlah_terima) AS total_masuk
                    FROM stok_masuk_line sml
                    JOIN stok_masuk sm ON sm.id = sml.stok_masuk_id
                    WHERE sm.state = 'posted'
                    GROUP BY sm.tanggal_terima::date, sml.bahan_id
                ),
                keluar AS (
                    SELECT sk.tanggal::date AS tanggal, skl.bahan_id, SUM(skl.jumlah_pakai) AS total_keluar
                    FROM stok_keluar_line skl
                    JOIN stok_keluar sk ON sk.id = skl.stok_keluar_id
                    WHERE sk.state = 'confirmed'
                    GROUP BY sk.tanggal::date, skl.bahan_id
                ),
                future_masuk AS (
                    SELECT tb.tanggal, tb.bahan_id, COALESCE(SUM(sml.jumlah_terima), 0) AS total
                    FROM tanggal_bahan tb
                    LEFT JOIN stok_masuk_line sml ON sml.bahan_id = tb.bahan_id
                    JOIN stok_masuk sm ON sm.id = sml.stok_masuk_id
                        AND sm.state = 'posted'
                    WHERE sm.tanggal_terima::date > tb.tanggal
                    GROUP BY tb.tanggal, tb.bahan_id
                ),
                future_keluar AS (
                    SELECT tb.tanggal, tb.bahan_id, COALESCE(SUM(skl.jumlah_pakai), 0) AS total
                    FROM tanggal_bahan tb
                    LEFT JOIN stok_keluar_line skl ON skl.bahan_id = tb.bahan_id
                    JOIN stok_keluar sk ON sk.id = skl.stok_keluar_id
                        AND sk.state = 'confirmed'
                    WHERE sk.tanggal::date > tb.tanggal
                    GROUP BY tb.tanggal, tb.bahan_id
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY tb.tanggal DESC, tb.bahan_id) AS id,
                    tb.tanggal,
                    TO_CHAR(tb.tanggal, 'YYYY-MM-DD') AS tanggal_group,
                    DATE_TRUNC('month', tb.tanggal)::date AS bulan,
                    TO_CHAR(DATE_TRUNC('month', tb.tanggal)::date, 'YYYY-MM') AS bulan_group,
                    tb.bahan_id,
                    bb.kategori,
                    bb.satuan,
                    COALESCE(m.total_masuk, 0) AS total_masuk,
                    COALESCE(k.total_keluar, 0) AS total_keluar,
                    bb.saldo_stok - COALESCE(fm.total, 0) + COALESCE(fk.total, 0) AS saldo_akhir
                FROM tanggal_bahan tb
                JOIN bahan_baku bb ON bb.id = tb.bahan_id
                LEFT JOIN masuk m ON m.tanggal = tb.tanggal AND m.bahan_id = tb.bahan_id
                LEFT JOIN keluar k ON k.tanggal = tb.tanggal AND k.bahan_id = tb.bahan_id
                LEFT JOIN future_masuk fm ON fm.tanggal = tb.tanggal AND fm.bahan_id = tb.bahan_id
                LEFT JOIN future_keluar fk ON fk.tanggal = tb.tanggal AND fk.bahan_id = tb.bahan_id
            )
        """)


class LaporanStokBulanan(models.Model):
    _name = 'laporan.stok.bulanan'
    _description = 'Laporan Bulanan Penggunaan Bahan Baku'
    _auto = False
    _order = 'bulan desc, bahan_id'

    bulan = fields.Date(string="Bulan", readonly=True)
    bulan_group = fields.Char(string="Bulan Rekap", readonly=True)
    tanggal = fields.Date(string="Tanggal", readonly=True)
    tanggal_group = fields.Char(string="Tanggal Rekap", readonly=True)
    bahan_id = fields.Many2one('bahan.baku', string="Bahan Baku", readonly=True)
    kategori = fields.Selection([
        ('bahan_kering', 'Bahan Kering'),
        ('bahan_basah', 'Bahan Basah'),
        ('cairan', 'Cairan'),
        ('lainnya', 'Lainnya'),
    ], string="Kategori", readonly=True)
    satuan = fields.Selection([
        ('gr', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Mililiter'),
        ('l', 'Liter'),
        ('pcs', 'Pcs'),
    ], string="Satuan", readonly=True)
    total_masuk = fields.Float(string="Total Stok Masuk", readonly=True)
    total_keluar = fields.Float(string="Total Stok Keluar", readonly=True)
    rata_rata_pemakaian_harian = fields.Float(string="Rata-rata Pemakaian Harian", readonly=True)
    saldo_akhir = fields.Float(string="Saldo Akhir Bulan", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW laporan_stok_bulanan AS (
                WITH bulan_bahan AS (
                    SELECT DATE_TRUNC('month', sm.tanggal_terima)::date AS bulan, sml.bahan_id
                    FROM stok_masuk_line sml
                    JOIN stok_masuk sm ON sm.id = sml.stok_masuk_id
                    WHERE sm.state = 'posted'
                    UNION
                    SELECT DATE_TRUNC('month', sk.tanggal)::date AS bulan, skl.bahan_id
                    FROM stok_keluar_line skl
                    JOIN stok_keluar sk ON sk.id = skl.stok_keluar_id
                    WHERE sk.state = 'confirmed'
                ),
                masuk AS (
                    SELECT DATE_TRUNC('month', sm.tanggal_terima)::date AS bulan, sml.bahan_id, SUM(sml.jumlah_terima) AS total_masuk
                    FROM stok_masuk_line sml
                    JOIN stok_masuk sm ON sm.id = sml.stok_masuk_id
                    WHERE sm.state = 'posted'
                    GROUP BY DATE_TRUNC('month', sm.tanggal_terima)::date, sml.bahan_id
                ),
                keluar AS (
                    SELECT DATE_TRUNC('month', sk.tanggal)::date AS bulan, skl.bahan_id, SUM(skl.jumlah_pakai) AS total_keluar
                    FROM stok_keluar_line skl
                    JOIN stok_keluar sk ON sk.id = skl.stok_keluar_id
                    WHERE sk.state = 'confirmed'
                    GROUP BY DATE_TRUNC('month', sk.tanggal)::date, skl.bahan_id
                ),
                future_masuk AS (
                    SELECT bbn.bulan, bbn.bahan_id, COALESCE(SUM(sml.jumlah_terima), 0) AS total
                    FROM bulan_bahan bbn
                    LEFT JOIN stok_masuk_line sml ON sml.bahan_id = bbn.bahan_id
                    JOIN stok_masuk sm ON sm.id = sml.stok_masuk_id
                        AND sm.state = 'posted'
                    WHERE sm.tanggal_terima::date >= (bbn.bulan + INTERVAL '1 month')::date
                    GROUP BY bbn.bulan, bbn.bahan_id
                ),
                future_keluar AS (
                    SELECT bbn.bulan, bbn.bahan_id, COALESCE(SUM(skl.jumlah_pakai), 0) AS total
                    FROM bulan_bahan bbn
                    LEFT JOIN stok_keluar_line skl ON skl.bahan_id = bbn.bahan_id
                    JOIN stok_keluar sk ON sk.id = skl.stok_keluar_id
                        AND sk.state = 'confirmed'
                    WHERE sk.tanggal::date >= (bbn.bulan + INTERVAL '1 month')::date
                    GROUP BY bbn.bulan, bbn.bahan_id
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY bbn.bulan DESC, bbn.bahan_id) AS id,
                    bbn.bulan,
                    TO_CHAR(bbn.bulan, 'YYYY-MM') AS bulan_group,
                    bbn.bulan AS tanggal,
                    TO_CHAR(bbn.bulan, 'YYYY-MM-DD') AS tanggal_group,
                    bbn.bahan_id,
                    bb.kategori,
                    bb.satuan,
                    COALESCE(m.total_masuk, 0) AS total_masuk,
                    COALESCE(k.total_keluar, 0) AS total_keluar,
                    COALESCE(k.total_keluar, 0)
                        / EXTRACT(DAY FROM (bbn.bulan + INTERVAL '1 month' - INTERVAL '1 day')) AS rata_rata_pemakaian_harian,
                    bb.saldo_stok - COALESCE(fm.total, 0) + COALESCE(fk.total, 0) AS saldo_akhir
                FROM bulan_bahan bbn
                JOIN bahan_baku bb ON bb.id = bbn.bahan_id
                LEFT JOIN masuk m ON m.bulan = bbn.bulan AND m.bahan_id = bbn.bahan_id
                LEFT JOIN keluar k ON k.bulan = bbn.bulan AND k.bahan_id = bbn.bahan_id
                LEFT JOIN future_masuk fm ON fm.bulan = bbn.bulan AND fm.bahan_id = bbn.bahan_id
                LEFT JOIN future_keluar fk ON fk.bulan = bbn.bulan AND fk.bahan_id = bbn.bahan_id
            )
        """)
