"""Extracción de la tabla de PIEZAS de un peritaje GT Estimate (PDF).

Estrategia híbrida, validada con un peritaje real:
- Código, unidades y precios: del texto real del PDF (exactos).
- Descripción: del texto real; si está vacía (GT Estimate dibuja las líneas
  con tildes o ñ), OCR con Tesseract sobre el recorte de esa celda.

Todo se ejecuta en local: ningún dato sale del servidor.
"""
import re

try:
    import pymupdf
except ImportError:  # pragma: no cover
    pymupdf = None

try:
    import pytesseract
    from PIL import Image
except ImportError:  # pragma: no cover
    pytesseract = None

# Columnas de la tabla, en puntos PDF (medidas sobre un peritaje real A4)
X_MARCA = (25, 50)       # marcas "I" de las filas hijas
X_CODIGO = (50, 138)
X_DESC = (139, 336)
X_UDS = (336, 360)
X_PRECIO = (370, 416)
X_TOTAL = (540, 580)
TOL_FILA = 3             # palabras a menos de 3 pt en vertical = misma línea
OCR_DPI = 400

# Caracteres que pueden aparecer en una descripción; el resto es ruido del OCR
_RUIDO_OCR = re.compile(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ ,.\-/()%+]")


class GtParserError(Exception):
    pass


def _en(x, rango):
    return rango[0] <= x < rango[1]


def _numero(texto):
    """'1.234,56' -> 1234.56 ; '' -> 0.0"""
    texto = (texto or "").replace("€", "").replace("h", "").strip()
    if not texto:
        return 0.0
    try:
        return float(texto.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def _limpiar_ocr(texto):
    texto = _RUIDO_OCR.sub("", texto)
    return " ".join(texto.split())


def _ocr(page, rect):
    pix = page.get_pixmap(dpi=OCR_DPI, clip=rect)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    texto = pytesseract.image_to_string(img, lang="spa", config="--psm 7")
    return _limpiar_ocr(texto)


def _zona_piezas(page):
    """(y_inicio, y_fin) de la tabla de piezas en la página, o None."""
    palabras = sorted(page.get_text("words"), key=lambda w: (w[1], w[0]))
    cabeceras_uds = [w[1] for w in palabras if w[4] == "Uds."]
    inicio = None
    for w in palabras:
        es_tabla = any(0 < y - w[1] < 20 for y in cabeceras_uds)
        if inicio is None and w[0] < 30 and w[4] == "Piezas" and es_tabla:
            inicio = w[3] + 12  # saltamos la fila de cabecera
        elif inicio is not None and w[0] < 30 and w[1] > inicio and w[4] in ("Mano", "Pintura", "Resumen"):
            return inicio, w[1] - 2
    if inicio is None:
        return None
    return inicio, page.rect.height - 60


def _lineas(page, y0, y1):
    palabras = [w for w in page.get_text("words") if y0 <= w[1] < y1]
    palabras.sort(key=lambda w: (w[1], w[0]))
    grupos = []
    for w in palabras:
        if grupos and abs(grupos[-1]["y0"] - w[1]) <= TOL_FILA:
            grupos[-1]["words"].append(w)
        else:
            grupos.append({"y0": w[1], "words": [w]})
    return grupos


def _tipo_linea(codigo):
    """Clasifica la línea según su código y lo devuelve limpio."""
    tokens = codigo.split()
    if not tokens:
        return "no_ref", ""
    if codigo.upper().startswith("SIN REFERENCIA"):
        return "no_ref", ""
    if tokens[0].upper() == "USADO":
        return "used", ""
    if "RECUPERADA" in (t.upper() for t in tokens):
        limpio = " ".join(t for t in tokens if t.upper() != "RECUPERADA")
        return "recovered", limpio
    if tokens[0].startswith(("GtT", "GtP")) or (tokens[0].isdigit() and len(tokens[0]) < 4):
        return "internal", codigo
    return "ref", codigo


def extract_parts(pdf_bytes):
    """Devuelve una lista de dicts, una por pieza del peritaje."""
    if pymupdf is None or pytesseract is None:
        raise GtParserError("Faltan las librerías pymupdf y/o pytesseract en el servidor.")
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise GtParserError(f"No se pudo abrir el PDF: {e}")

    piezas = []
    for n_pag, page in enumerate(doc, 1):
        zona = _zona_piezas(page)
        if not zona:
            continue
        filas = []
        for ln in _lineas(page, *zona):
            ws = ln["words"]
            marca = " ".join(w[4] for w in ws if _en(w[0], X_MARCA))
            cod = " ".join(w[4] for w in ws if _en(w[0], X_CODIGO))
            desc = " ".join(w[4] for w in ws if _en(w[0], X_DESC))
            uds = " ".join(w[4] for w in ws if _en(w[0], X_UDS))
            precio = " ".join(w[4] for w in ws if _en(w[0], X_PRECIO))
            # Línea de continuación: solo trae más código (p. ej. "RECUPERADA", "(ALT)")
            if filas and cod and not desc and not uds:
                filas[-1]["cod"] += " " + cod
                continue
            filas.append({"y0": ln["y0"], "marca": marca, "cod": cod,
                          "desc": desc, "uds": uds, "precio": precio})

        grupo = ""
        for f in filas:
            fuente = "text"
            desc = f["desc"]
            if not desc:
                rect = pymupdf.Rect(X_DESC[0], f["y0"] - 1, X_DESC[1], f["y0"] + 9.5)
                desc = _ocr(page, rect)
                fuente = "ocr"
            # Fila de agrupación (sin cantidad): título para las filas hijas "I"
            if not f["uds"]:
                grupo = desc
                continue
            if f["marca"] == "I" and grupo:
                desc = f"{grupo} - {desc}"
            else:
                grupo = ""
            tipo, codigo = _tipo_linea(f["cod"])
            piezas.append({
                "page": n_pag,
                "code": codigo,
                "raw_code": f["cod"],
                "description": desc,
                "source": fuente,
                "line_type": tipo,
                "qty": _numero(f["uds"]),
                "price": _numero(f["precio"]),
            })
    doc.close()
    return piezas
