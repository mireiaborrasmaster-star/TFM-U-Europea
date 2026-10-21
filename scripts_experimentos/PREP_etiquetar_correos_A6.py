# -*- coding: utf-8 -*-
"""
PREP_etiquetar_correos_A6.py · prepara los 105 correos para etiquetar a mano
=============================================================================

PARA QUE
    La cuarta pieza de A6 decide si un mensaje que entra al buzon es una
    solicitud comercial o es otra cosa: un proveedor que ofrece sus
    servicios, un curriculum, una invitacion a un congreso, una factura.

    Esa clase NO EXISTE EN EL CRM, porque alli solo esta lo que llego a
    convertirse en algo. Los unicos ejemplos posibles son estos 105 correos.

POR QUE NO VALE LA LISTA DE PALABRAS
    Se intento detectarlos con una lista de terminos y SALIO MAL. La lista
    marcaba 15 correos; al mirar el contexto uno a uno, **al menos doce eran
    clientes**:

       · diez decian «proveedor» hablando de SUS PROPIOS proveedores
         («la caja la fabrica nuestro proveedor, necesitamos saber que
          ensayos debe superar») -> eso es un cliente pidiendo un ensayo
       · uno decia «demostraciones practicas del producto»
       · uno decia «beca» de pasada y pedia ensayos de migracion

    Un modelo entrenado sobre esa lista aprende a detectar la palabra
    «proveedor», que en este corpus es senal COMERCIAL, o sea lo contrario
    de lo que se busca. Queda como error X25.

    De ahi que haga falta el juicio de una persona de la casa. No es por
    rigor academico: es que la etiqueta automatica estaba del reves.

QUE GENERA
    datos/01_limpio/etiquetar_correos_A6.xlsx

    Una hoja de instrucciones y otra con los 105 correos, su texto y una
    columna vacia que rellenar con SI o NO. Nada mas.

COMO SE EJECUTA
    python scripts/PREP_etiquetar_correos_A6.py
"""

import sys
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 04-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
CORPUS = RAIZ / "datos" / "01_limpio" / "entradas_inbound_50_anon.csv"
SALIDA = RAIZ / "datos" / "01_limpio" / "etiquetar_correos_A6.xlsx"

INSTRUCCIONES = [
    ("QUE HAY QUE HACER", ""),
    ("", "Ve a la hoja «correos». Hay 105 filas. En la columna "
         "«es_comercial» escribe SI o NO."),
    ("", "Nada mas. No hace falta tocar ninguna otra columna."),
    ("", ""),
    ("LA PREGUNTA, EXACTAMENTE", ""),
    ("", "¿Esta persona podria acabar contratando algo a Empresa?"),
    ("", ""),
    ("ESCRIBE «SI» CUANDO", ""),
    ("", "Pide un ensayo, un analisis, un estudio o asesoramiento"),
    ("", "Pregunta por una norma que tiene que cumplir"),
    ("", "Tiene un problema tecnico con un envase o un material"),
    ("", "Pide presupuesto o plazos de algo que hacemos"),
    ("", "Pregunta si podemos ayudarle, aunque no sepa con que"),
    ("", ""),
    ("ESCRIBE «NO» CUANDO", ""),
    ("", "Nos OFRECE algo: servicios, software, posicionamiento web"),
    ("", "Manda un curriculum o pide practicas"),
    ("", "Es una factura, un recibo o algo administrativo"),
    ("", "Es una newsletter o publicidad"),
    ("", "Nos invita a un congreso o a una feria para que paguemos"),
    ("", ""),
    ("LOS CASOS QUE CONFUNDEN  ·  leelos antes de empezar", ""),
    ("", "«Proveedor» NO significa que el correo sea de un proveedor."),
    ("", "   Casi siempre es un CLIENTE hablando de SUS proveedores."),
    ("", "   Ej.: «la caja la fabrica nuestro proveedor, ¿que ensayos"),
    ("", "   debe superar?» -> eso es SI, es un cliente."),
    ("", ""),
    ("", "Alguien que propone COLABORAR o un proyecto conjunto:"),
    ("", "   si de ahi puede salir trabajo facturable, SI."),
    ("", "   Si es solo difusion o un acuerdo sin contraprestacion, NO."),
    ("", ""),
    ("", "Un socio o una asociacion que pregunta por un servicio: SI."),
    ("", "   Lo que importa es si puede acabar en una oportunidad,"),
    ("", "   no si paga tarifa de socio."),
    ("", ""),
    ("SI DUDAS", ""),
    ("", "Escribe DUDA en vez de SI o NO. Mejor eso que forzar una"),
    ("", "respuesta: las dudas se cuentan aparte y tambien son un dato."),
    ("", ""),
    ("CUANTO LLEVA", ""),
    ("", "Unos veinte minutos. Los correos estan recortados a lo que"),
    ("", "hace falta para decidir."),
    ("", ""),
    ("CUANDO TERMINES", ""),
    ("", "Guarda el fichero donde esta y dimelo. Con eso la cuarta"),
    ("", "pieza de A6 pasa de «no se puede medir» a tener una cifra."),
]


def main():
    if not CORPUS.exists():
        raise SystemExit(f"   No encuentro {CORPUS.name}. Lanza antes\n"
                         f"   F6_A6_corpus_correos.py --guardar")

    print()
    print("=" * 74)
    print(f"PREP · hoja para etiquetar los correos  ·  {VERSION_SCRIPT}")
    print("=" * 74)
    print()

    d = pd.read_csv(CORPUS, sep=";")
    d["cuerpo"] = d.cuerpo.fillna("").astype(str)

    # El texto se recorta: para decidir si es comercial basta con el
    # principio, y un correo de 600 palabras en una celda no se lee.
    hoja = pd.DataFrame({
        "id": d.id,
        "es_comercial": "",
        "idioma": d.idioma,
        "palabras": d.palabras,
        "texto": d.cuerpo.str.slice(0, 1200),
        "sigue": d.cuerpo.str.len().gt(1200).map({True: "...(cortado)", False: ""}),
    })

    ins = pd.DataFrame(INSTRUCCIONES, columns=["", " "])

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(SALIDA, engine="openpyxl") as w:
        ins.to_excel(w, sheet_name="LEEME", index=False)
        hoja.to_excel(w, sheet_name="correos", index=False)
        # anchos y ajuste de linea, que si no es ilegible
        hl, hc = w.sheets["LEEME"], w.sheets["correos"]
        hl.column_dimensions["A"].width = 44
        hl.column_dimensions["B"].width = 72
        for col, ancho in (("A", 9), ("B", 14), ("C", 8), ("D", 10),
                           ("E", 110), ("F", 13)):
            hc.column_dimensions[col].width = ancho
        from openpyxl.styles import Alignment, Font, PatternFill
        hc.freeze_panes = "C2"
        amarillo = PatternFill("solid", fgColor="FFF2CC")
        for fila in range(2, len(hoja) + 2):
            hc[f"B{fila}"].fill = amarillo
            hc[f"E{fila}"].alignment = Alignment(wrap_text=True, vertical="top")
            hc.row_dimensions[fila].height = 95
        for c in "ABCDEF":
            hc[f"{c}1"].font = Font(bold=True)
        for fila in range(1, len(ins) + 2):
            hl[f"A{fila}"].font = Font(bold=True)
            hl[f"B{fila}"].alignment = Alignment(wrap_text=True)

    print(f"   [ok] {SALIDA.name}")
    print(f"        {len(hoja)} correos · la columna B es la que se rellena")
    print()
    print("   Esta en datos/01_limpio/")
    print()
    print("   Cuando este relleno, lanza:")
    print("      python scripts/F6_A6_agente_recepcion.py --guardar")
    print("   y usara tus etiquetas en vez de la lista de palabras.")
    print()


if __name__ == "__main__":
    main()
