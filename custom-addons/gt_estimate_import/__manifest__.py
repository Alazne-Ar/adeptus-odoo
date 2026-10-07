{
    "name": "GT Estimate Import",
    "version": "18.0.2.0.0",
    "summary": "Extrae las piezas de peritajes GT Estimate (PDF) y genera pedidos de compra",
    "description": """
Lee la tabla de piezas de un peritaje de GT Estimate en PDF:
códigos, unidades y precios desde el texto del PDF, y las descripciones
dibujadas con OCR local (Tesseract). Tras revisarlas, genera un pedido
de compra en borrador. Ningún dato sale del servidor.
""",
    "category": "Purchases",
    "author": "Alazne",
    "license": "LGPL-3",
    "depends": ["purchase"],
    "external_dependencies": {"python": ["pymupdf", "pytesseract"]},
    "data": [
        "security/ir.model.access.csv",
        "data/product_data.xml",
        "views/gt_estimate_import_views.xml",
    ],
    "installable": True,
    "application": False,
}
