"""
Prueba de extracción híbrida de la tabla de PIEZAS de un peritaje GT Estimate.

- Código, unidades y precios: del texto real del PDF (exactos).
- Descripción: del texto real si existe; si no (está dibujada), OCR con
  Tesseract sobre un recorte de esa celda.
- Además, hace OCR de TODAS las descripciones que sí son texto, para medir
  cuánto acierta Tesseract comparando con el valor real.

Uso:
    python3 prueba_ocr.py peritaje_final.pdf
"""
import sys
import unicodedata

import pymupdf
import pytesseract
from PIL import Image

# Columnas de la tabla (en puntos PDF, medidas sobre el peritaje real)
X_CODIGO = (50, 138)
X_DESC = (139, 336)
X_UDS = (336, 360)
X_PRECIO = (370, 416)
X_TOTAL = (540, 580)
TOL_FILA = 3  # palabras con y0 a menos de 3 pt se consideran la misma línea


def en(x, rango):
    return rango[0] <= x < rango[1]


def ocr_recorte(page, rect, dpi=400):
    pix = page.get_pixmap(dpi=dpi, clip=rect)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    txt = pytesseract.image_to_string(img, lang="spa", config="--psm 7")
    return " ".join(txt.split())


def normalizar(s):
    return " ".join(s.split()).strip()


def zona_piezas(page):
    """Devuelve (y_inicio, y_fin) de la tabla de piezas en la página, o None."""
    palabras = sorted(page.get_text("words"), key=lambda w: (w[1], w[0]))
    cabeceras_uds = [w[1] for w in palabras if w[4] == "Uds."]
    inicio = fin = None
    for w in palabras:
        es_tabla = any(0 < y - w[1] < 20 for y in cabeceras_uds)  # "Piezas" seguida de cabecera con "Uds."
        if w[0] < 30 and w[4] == "Piezas" and inicio is None and es_tabla:
            inicio = w[3] + 12  # saltamos la fila de cabecera
        elif inicio is not None and w[0] < 30 and w[4] in ("Mano", "Pintura", "Resumen") and w[1] > inicio:
            fin = w[1] - 2
            break
    if inicio is None:
        return None
    return inicio, fin or page.rect.height - 60


def lineas(page, y0, y1):
    """Agrupa las palabras de la zona en líneas por su coordenada y."""
    palabras = [w for w in page.get_text("words") if y0 <= w[1] < y1]
    palabras.sort(key=lambda w: (w[1], w[0]))
    grupos = []
    for w in palabras:
        if grupos and abs(grupos[-1]["y0"] - w[1]) <= TOL_FILA:
            grupos[-1]["words"].append(w)
            grupos[-1]["y1"] = max(grupos[-1]["y1"], w[3])
        else:
            grupos.append({"y0": w[1], "y1": w[3], "words": [w]})
    return grupos


def filas(page, y0, y1):
    """Une líneas de continuación (solo código, sin descripción ni cantidades)."""
    resultado = []
    for ln in lineas(page, y0, y1):
        cod = [w[4] for w in ln["words"] if en(w[0], X_CODIGO)]
        desc = [w[4] for w in ln["words"] if en(w[0], X_DESC)]
        uds = [w[4] for w in ln["words"] if en(w[0], X_UDS)]
        precio = [w[4] for w in ln["words"] if en(w[0], X_PRECIO)]
        total = [w[4] for w in ln["words"] if en(w[0], X_TOTAL)]
        es_continuacion = resultado and cod and not desc and not uds
        if es_continuacion:
            resultado[-1]["codigo"] += " " + " ".join(cod)
            resultado[-1]["y1"] = ln["y1"]
            continue
        resultado.append({
            "y0": ln["y0"], "y1": ln["y1"],
            "codigo": " ".join(cod), "desc_texto": " ".join(desc),
            "uds": " ".join(uds), "precio": " ".join(precio), "total": " ".join(total),
        })
    return resultado


def main(ruta):
    doc = pymupdf.open(ruta)
    todas = []
    for n, page in enumerate(doc, 1):
        zona = zona_piezas(page)
        if not zona:
            continue
        for f in filas(page, *zona):
            rect = pymupdf.Rect(X_DESC[0], f["y0"] - 1, X_DESC[1], f["y0"] + 9.5)
            f["desc_ocr"] = ocr_recorte(page, rect)
            f["pagina"] = n
            todas.append(f)

    print(f"{'Pág':<4}{'Código':<26}{'Desc. (texto)':<34}{'Desc. (OCR)':<34}{'Uds':<6}{'Precio':>9}")
    print("-" * 113)
    for f in todas:
        print(f"{f['pagina']:<4}{f['codigo'][:25]:<26}{f['desc_texto'][:33]:<34}"
              f"{f['desc_ocr'][:33]:<34}{f['uds']:<6}{f['precio']:>9}")

    # Precisión del OCR sobre las filas que sí tienen texto real
    con_texto = [f for f in todas if f["desc_texto"]]
    aciertos = [f for f in con_texto if normalizar(f["desc_ocr"]) == normalizar(f["desc_texto"])]
    sin_texto = [f for f in todas if not f["desc_texto"]]
    print()
    print(f"Filas de piezas: {len(todas)}")
    print(f"  Descripción como texto real: {len(con_texto)}")
    print(f"  Descripción dibujada (solo OCR): {len(sin_texto)}")
    if con_texto:
        print(f"Precisión OCR en filas comprobables: {len(aciertos)}/{len(con_texto)} exactas")
        for f in con_texto:
            if f not in aciertos:
                print(f"  ✗ real={f['desc_texto']!r}  ocr={f['desc_ocr']!r}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 prueba_ocr.py peritaje.pdf")
        sys.exit(1)
    main(sys.argv[1])
