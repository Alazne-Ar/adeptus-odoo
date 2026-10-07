import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services import gt_parser

LINE_TYPES = [
    ("ref", "Referencia"),
    ("used", "Usado"),
    ("recovered", "Recuperada"),
    ("no_ref", "Sin referencia"),
    ("internal", "Interna GT"),
]


class GtEstimateImport(models.Model):
    _name = "gt.estimate.import"
    _description = "Peritaje GT Estimate importado"
    _order = "create_date desc"

    name = fields.Char("Peritaje", required=True, default=lambda self: _("Nuevo peritaje"))
    pdf_file = fields.Binary("PDF del peritaje", attachment=True)
    pdf_filename = fields.Char("Nombre del archivo")
    state = fields.Selection(
        [("draft", "Borrador"), ("extracted", "Extraído"), ("done", "Pedido creado")],
        default="draft", required=True, string="Estado",
    )
    partner_id = fields.Many2one("res.partner", "Proveedor")
    line_ids = fields.One2many("gt.estimate.import.line", "import_id", "Piezas")
    purchase_id = fields.Many2one("purchase.order", "Pedido de compra", readonly=True)
    notes = fields.Text("Resultado de la extracción", readonly=True)
    order_total = fields.Float("Total a pedir", compute="_compute_order_total")

    @api.depends("line_ids.to_order", "line_ids.qty", "line_ids.price")
    def _compute_order_total(self):
        for rec in self:
            rec.order_total = sum(l.qty * l.price for l in rec.line_ids if l.to_order)

    @api.onchange("pdf_filename")
    def _onchange_pdf_filename(self):
        if self.pdf_filename and self.name == _("Nuevo peritaje"):
            self.name = self.pdf_filename.rsplit(".", 1)[0]

    def action_extract(self):
        self.ensure_one()
        if not self.pdf_file:
            raise UserError(_("Sube primero el PDF del peritaje."))
        try:
            piezas = gt_parser.extract_parts(base64.b64decode(self.pdf_file))
        except gt_parser.GtParserError as e:
            raise UserError(str(e))
        if not piezas:
            raise UserError(_("No se ha encontrado ninguna tabla de piezas en el PDF."))

        self.line_ids.unlink()
        self.line_ids = [
            fields.Command.create({
                "sequence": i,
                "page": p["page"],
                "code": p["code"],
                "raw_code": p["raw_code"],
                "description": p["description"],
                "source": p["source"],
                "line_type": p["line_type"],
                "qty": p["qty"],
                "price": p["price"],
                "to_order": p["line_type"] == "ref",
            })
            for i, p in enumerate(piezas, 1)
        ]
        n_ocr = sum(1 for p in piezas if p["source"] == "ocr")
        self.notes = _(
            "%(total)s piezas extraídas: %(texto)s desde el texto del PDF y %(ocr)s por OCR. "
            "Revisa sobre todo las líneas marcadas como OCR.",
            total=len(piezas), texto=len(piezas) - n_ocr, ocr=n_ocr,
        )
        self.state = "extracted"

    def action_create_purchase(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Elige el proveedor antes de crear el pedido."))
        lineas = self.line_ids.filtered("to_order")
        if not lineas:
            raise UserError(_("No hay ninguna pieza marcada para pedir."))
        producto = self.env.ref("gt_estimate_import.product_pieza_peritaje")
        pedido = self.env["purchase.order"].create({
            "partner_id": self.partner_id.id,
            "origin": self.name,
            "order_line": [
                fields.Command.create({
                    "product_id": producto.id,
                    "name": f"[{l.code}] {l.description}" if l.code else l.description,
                    "product_qty": l.qty or 1.0,
                    "price_unit": l.price,
                })
                for l in lineas
            ],
        })
        self.write({"purchase_id": pedido.id, "state": "done"})
        return self.action_view_purchase()

    def action_view_purchase(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "res_id": self.purchase_id.id,
            "view_mode": "form",
        }

    def action_reset(self):
        self.write({"state": "draft"})


class GtEstimateImportLine(models.Model):
    _name = "gt.estimate.import.line"
    _description = "Pieza de un peritaje GT Estimate"
    _order = "sequence, id"

    import_id = fields.Many2one("gt.estimate.import", required=True, ondelete="cascade")
    sequence = fields.Integer()
    page = fields.Integer("Pág.")
    to_order = fields.Boolean("Pedir")
    code = fields.Char("Referencia")
    raw_code = fields.Char("Código en el PDF")
    description = fields.Char("Descripción")
    source = fields.Selection([("text", "Texto"), ("ocr", "OCR")], "Origen")
    line_type = fields.Selection(LINE_TYPES, "Tipo")
    qty = fields.Float("Uds.", digits="Product Unit of Measure")
    price = fields.Float("Precio peritaje", digits="Product Price")
    subtotal = fields.Float("Subtotal", compute="_compute_subtotal")

    @api.depends("qty", "price")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.price
