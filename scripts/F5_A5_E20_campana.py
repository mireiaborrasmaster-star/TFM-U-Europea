"""
A5 · CORREOS DE CAMPANA
========================
Escribe el correo de una campana a muchas empresas, personalizando el enlace
entre el mensaje de la campana y la actividad de cada una.

EN QUE SE DIFERENCIA DE F5_A5_E19_generar_correos.py
-------------------------------------
  F5_A5_E19_generar_correos.py   ELIGE el servicio (emparejamiento semantico) y escribe.
  F5_A5_E20_campana.py   El servicio y el disparador VIENEN DADOS en el brief de
                  campana. El modelo solo conecta ese mensaje con la empresa.

El cambio viene de un hallazgo y de una observacion del negocio.

El hallazgo (E19): la parte de elegir es el eslabon debil. A un fabricante de
aisladores ceramicos se le propuso caracterizacion de materiales de envase, y
eso no se arregla redactando mejor.

La observacion: en Empresa una campana la decide una persona. Se elige un tema,
se prepara el material y se lanza. Lo que no escala no es decidir el tema sino
escribir cientos de correos que conecten ese tema con cada empresa.

QUE APORTA ESTO A LA FUNDAMENTACION
-----------------------------------
Todo lo que el correo afirma sobre normativa, plazos o contenido tecnico sale
del brief, que ha escrito una persona. El modelo no necesita inventarse
contexto de mercado porque se lo damos. Lo unico que aporta el es el enlace con
la actividad de la empresa, y eso si se verifica contra el texto de su web.

Era el defecto de la version anterior: el propio ejemplo del prompt afirmaba
cosas sobre el mercado que no estaban en ninguna evidencia, y el modelo aprendia
de ahi que inventar contexto es aceptable.

LA PREGUNTA QUE RESPONDE EL EXPERIMENTO
---------------------------------------
Hoy la campana se lanza con el MISMO texto para todas las empresas. Esa es la
linea base, y es exigente: un correo escrito por una persona.

    ¿Personalizar automaticamente aporta algo frente a mandar el mismo correo
    a todo el mundo?

Y se puede medir. Si los correos generados se parecen entre si, el modelo esta
regurgitando el brief y no aporta nada sobre el generico. Si varian, hay que
comprobar que la variacion viene de la web de cada empresa y no de su
imaginacion. Son dos metricas distintas y las dos hacen falta:

    PERSONALIZACION  cuanto del correo procede de la web de ESTA empresa y no
                     del brief (que es comun a todos)
    REDUNDANCIA      cuanto se parecen los correos entre si. El correo generico
                     tiene redundancia 1,00 por definicion: es el mismo.

ABSTENCION
----------
El brief declara a quien NO le aplica la campana. Si la empresa no encaja, el
modelo debe decirlo en lugar de forzar el encaje. Es la misma logica de la
politica de confianza de E18: reconocer cuando no se debe actuar es parte del
trabajo del agente, no un fallo.

Uso en Colab (necesita GPU):
    !python scripts/F5_A5_E20_campana.py --campana C01 --muestra 40
"""

import argparse
import re
import sys
import warnings
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v2 · 10-10-2026 · el brief se lee del Word si existe"

RAIZ = Path(__file__).resolve().parent.parent
# El brief de campana puede venir de dos sitios. Manda el Word: es el que
# edita la autora. El .md se queda como respaldo para que el guion siga
# funcionando aunque el Word no exista todavia.
CAMPANAS_WORD = RAIZ / "12_CAMPANAS.docx"
CAMPANAS_MD = RAIZ / "12_CAMPANAS.md"
DERIVADO = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent))
from F5_A5_E17_emparejar_lexico import sin_acentos  # noqa: E402
from F5_A5_E18_emparejar_semantico import MAX_CARACTERES  # noqa: E402
from F5_A5_E19_generar_correos import (raiz, terminos, SALUDOS, DESPEDIDAS, AGRADECE,  # noqa: E402
                        TIC_LECTURA, TIC_MARCADOR)

MARCA_ABSTENCION = "NO APLICA"


# ==========================================================================
# Lectura del brief
# ==========================================================================
#
# EL BRIEF PUEDE VENIR DE TRES SITIOS, Y LOS TRES DAN EL MISMO TEXTO
#
#   1. Un Word con UNA TABLA POR CAMPANA. Es la forma recomendada y la que
#      la autora usa: no depende de ningun estilo de Word, la estructura
#      esta en la propia tabla y no se puede olvidar un campo porque las
#      filas ya estan puestas.
#   2. Un Word con encabezados de nivel 2. Se mantiene por si algun
#      documento viejo venia asi.
#   3. El .md de siempre, como respaldo.
#
# De los tres sale un texto con la MISMA forma —campos en **negrita**,
# vinetas con guion, tablas con barras—, de modo que el modelo recibe lo
# mismo pase lo que pase y cambiar de formato no mete una variable nueva en
# los resultados ya medidos. Lo comprueba `probar_lector_word.py`.
#
# Un .docx es un zip con XML dentro y se lee con la biblioteca estandar:
# anadir python-docx obligaria a instalarlo a quien reciba la entrega.

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Los campos de la tabla, en el orden en que salen al texto. Para cada uno:
# como se escribe en el texto final y de que forma se compone.
#   "campo"  ->  **Nombre.** valor
#   "lista"  ->  **Nombre.** y debajo una vineta por linea de la celda
#   "pares"  ->  **Nombre.** y debajo una tabla de dos columnas
#   "cabeza" ->  va en la tablita de Estado / Areas / Origen
CAMPOS = [
    ("campana", "cabecera", None),
    ("estado", "cabeza", "Estado"),
    ("areas empresa", "cabeza", "Áreas Empresa"),
    ("origen", "cabeza", "Origen"),
    ("disparador", "campo", "Disparador."),
    ("hitos", "campo", "Hitos."),
    ("puntos tecnicos", "lista",
     "Puntos técnicos que conviene tener en el radar."),
    ("que se entrega", "campo", "Qué se entrega."),
    ("que puede hacer empresa", "campo", "Qué puede hacer Empresa."),
    ("situacion actual", "campo", "Situación actual."),
    ("a quien le aplica", "campo", "A quién le aplica."),
    ("a quien no le aplica", "campo", "A quién NO le aplica."),
    ("como enlazar", "pares", "Cómo enlazar con la actividad de la empresa."),
    ("tono", "campo", "Tono."),
]


def _texto_parrafo(p):
    """El texto de un parrafo, conservando la negrita como **asi**.

    La negrita importa porque en el brief marca los campos —«**Disparador.**»,
    «**A quien NO le aplica.**»— y el modelo los usa para orientarse. Se
    reconstruye con los mismos asteriscos que tenia el .md para que el texto
    que recibe el modelo sea identico y el cambio de formato no altere
    ninguna medicion.
    """
    trozos = []
    for r in p.iter(W + "r"):
        texto = "".join(t.text or "" for t in r.iter(W + "t"))
        if not texto:
            continue
        rpr = r.find(W + "rPr")
        negrita = rpr is not None and rpr.find(W + "b") is not None
        if not negrita:
            trozos.append(texto)
            continue
        # En Word es muy facil dejar el espacio DENTRO de la negrita. Los
        # asteriscos van pegados al texto, nunca al espacio, porque
        # «**Disparador. **» no se lee como negrita.
        nucleo = texto.strip()
        if not nucleo:
            trozos.append(texto)
            continue
        izq = texto[:len(texto) - len(texto.lstrip())]
        der = texto[len(texto.rstrip()):]
        trozos.append(f"{izq}**{nucleo}**{der}")
    # Dos negritas seguidas se unen en una: «**a****b**» no es negrita.
    return "".join(trozos).replace("****", "")


def _nivel_de_encabezado(p):
    """2 si el parrafo es un encabezado de nivel 2, 3 si de nivel 3, 0 si no.

    Word en espanol llama a los estilos «Titulo 1», «Ttulo 1» y variantes
    segun la version, asi que se mira el numero final y no el nombre exacto.
    """
    ppr = p.find(W + "pPr")
    if ppr is None:
        return 0
    estilo = ppr.find(W + "pStyle")
    if estilo is None:
        return 0
    v = (estilo.get(W + "val") or "").lower()
    if not ("heading" in v or "titulo" in v or "ttulo" in v):
        return 0
    digitos = "".join(c for c in v if c.isdigit())
    return int(digitos) if digitos else 2


def _celdas(fila):
    """Las celdas de una fila, cada una con sus lineas ya limpias."""
    out = []
    for c in fila.findall(W + "tc"):
        lineas = [_texto_parrafo(p).strip() for p in c.findall(W + "p")]
        out.append([l for l in lineas if l])
    return out


def _clave(texto):
    """Normaliza un nombre de campo para compararlo: sin tildes, en minuscula
    y sin el punto final, de modo que «Qué se entrega.» y «que se entrega»
    sean lo mismo. La autora escribe en Word, no en codigo."""
    # Los asteriscos se quitan a proposito: el nombre del campo va en
    # negrita en el Word, de modo que llega como «**Campana**».
    t = sin_acentos(texto.lower()).replace("*", "").strip()
    return t.rstrip(".:").strip()


def _campana_de_tabla(tbl):
    """Convierte una tabla de Word en una campana, o devuelve None.

    Es una campana si alguna fila tiene a la izquierda «Campana» y a la
    derecha algo que empiece por un codigo del tipo C01.
    """
    valores = {}
    for fila in tbl.findall(W + "tr"):
        cs = _celdas(fila)
        if len(cs) < 2:
            continue
        nombre = _clave(" ".join(cs[0]))
        if nombre:
            valores[nombre] = cs[1]
    titulo = " ".join(valores.get("campana", []))
    m = re.match(r"\s*(C\d+)\s*·\s*(.+)", titulo)
    if not m:
        return None
    codigo, nombre = m.group(1), m.group(2).strip()

    # Se compone el texto con la misma forma que tenia el .md.
    lineas = [nombre, ""]
    cabeza = [(et, " ".join(valores[k]))
              for k, tipo, et in CAMPOS if tipo == "cabeza" and valores.get(k)]
    if cabeza:
        lineas += ["| | |", "|---|---|"]
        lineas += [f"| **{et}** | {v} |" for et, v in cabeza]
        lineas.append("")
    for k, tipo, et in CAMPOS:
        if tipo in ("cabecera", "cabeza") or not valores.get(k):
            continue
        celda = valores[k]
        if tipo == "campo":
            lineas += [f"**{et}** {' '.join(celda)}", ""]
        elif tipo == "lista":
            lineas.append(f"**{et}**")
            lineas.append("")
            lineas += [f"- {l.lstrip('-· ').strip()}" for l in celda]
            lineas.append("")
        elif tipo == "pares":
            lineas.append(f"**{et}**")
            lineas.append("")
            filas = []
            for l in celda:
                partes = re.split(r"\s*(?:→|->|\|)\s*", l, maxsplit=1)
                if len(partes) == 2:
                    filas.append((partes[0].strip(), partes[1].strip()))
            if filas:
                # La primera linea de la celda es la de encabezado, y debajo
                # va la fila separadora que el formato de tablas exige.
                lineas.append(f"| {filas[0][0]} | {filas[0][1]} |")
                lineas.append("|---|---|")
                lineas += [f"| {a} | {b} |" for a, b in filas[1:]]
            lineas.append("")
    return {"codigo": codigo, "nombre": nombre,
            "texto": "\n".join(lineas).strip()}


def campanas_de_docx(ruta):
    """Todas las campanas del Word, por tabla o por encabezado.

    Primero se buscan tablas, que es la forma recomendada. Si no hay
    ninguna, se recorre el documento por encabezados de nivel 2, que es
    como estaba escrito el .md.
    """
    with zipfile.ZipFile(ruta) as z:
        xml = z.read("word/document.xml")
    cuerpo = ElementTree.fromstring(xml).find(W + "body")

    por_tabla = []
    for tbl in cuerpo.iter(W + "tbl"):
        c = _campana_de_tabla(tbl)
        if c:
            por_tabla.append(c)
    if por_tabla:
        return por_tabla

    # Respaldo: el documento usa encabezados. Se reconstruye el texto plano
    # —con tablas y vinetas— y se trocea igual que el .md.
    lineas = []
    for hijo in cuerpo:
        if hijo.tag == W + "p":
            t = _texto_parrafo(hijo).strip()
            if not t:
                lineas.append("")
                continue
            n = _nivel_de_encabezado(hijo)
            lineas.append(("#" * n + " " + t) if n else t)
        elif hijo.tag == W + "tbl":
            for fila in hijo.findall(W + "tr"):
                celdas = [" ".join(c) for c in _celdas(fila)]
                lineas.append("| " + " | ".join(celdas) + " |")
            lineas.append("")
    return campanas_de_texto("\n".join(lineas))


def campanas_de_texto(texto):
    """Las campanas de un documento de texto, troceando por «## C01 · »."""
    out = []
    bloques = re.split(r"\n## (C\d+) · ", texto)[1:]
    for i in range(0, len(bloques), 2):
        cuerpo = re.split(r"\n## ", bloques[i + 1])[0].strip()
        # La raya que separa secciones en el .md no es parte del brief, y
        # hasta ahora se le colaba al modelo al final de las instrucciones.
        # Se quita para que el texto sea el mismo venga del .md o del Word.
        cuerpo = re.sub(r"\n+-{3,}\s*$", "", cuerpo).strip()
        out.append({"codigo": bloques[i],
                    "nombre": cuerpo.split("\n")[0].strip(),
                    "texto": cuerpo})
    return out


def leer_campana(codigo, ruta=None):
    """Devuelve la campana pedida, de donde este escrita.

    Orden de busqueda: lo que pase el usuario por --campanas, el Word y el
    .md como respaldo. Se imprime cual se ha usado, porque ejecutar con el
    documento equivocado y no enterarse es justo el error que hay que
    evitar.
    """
    candidatos = [Path(ruta)] if ruta else [CAMPANAS_WORD, CAMPANAS_MD]
    for p in candidatos:
        if not p.exists():
            continue
        if p.suffix.lower() == ".doc":
            sys.exit("\n".join([
                "",
                f"   {p.name} esta en el formato antiguo .doc, que no se puede",
                "   leer sin convertirlo. Abrelo en Word y guardalo como .docx",
                "   (Archivo > Guardar como > Documento de Word).",
                "",
            ]))
        if p.suffix.lower() == ".docx":
            print(f"   brief: {p.name} (Word)")
            campanas = campanas_de_docx(p)
        else:
            print(f"   brief: {p.name}")
            campanas = campanas_de_texto(p.read_text(encoding="utf-8"))
        for c in campanas:
            if c["codigo"] == codigo:
                return c
        if not campanas:
            # El fallo tipico: la tabla no tiene la fila «Campana», o el
            # titulo no lleva el estilo «Titulo 2». Sin una de las dos cosas
            # no hay nada que leer.
            sys.exit("\n".join([
                "",
                f"   En {p.name} no hay ninguna campana.",
                "",
                "   Cada campana es una TABLA cuya primera fila dice:",
                "",
                "       Campana | C01 · PPWR · Reglamento Europeo de...",
                "",
                "   Si prefieres el formato de titulos, el titulo tiene que",
                "   llevar el estilo «Titulo 2» de Word: ponerlo en negrita y",
                "   mas grande no basta. Y la plantilla en blanco va en su",
                "   propio documento, no en este.",
                "",
            ]))
        sys.exit("\n".join([
            "",
            f"   No existe la campana {codigo} en {p.name}.",
            f"   Las que hay: {', '.join(c['codigo'] for c in campanas)}",
            "",
        ]))
    sys.exit("\n".join([
        "",
        "   No encuentro el documento de campanas. Debe estar en",
        f"   {RAIZ}",
        "   con el nombre 12_CAMPANAS.docx (o 12_CAMPANAS.md), o pasarse",
        "   con --campanas RUTA.",
        "",
    ]))


# ==========================================================================
# El prompt
# ==========================================================================

INSTRUCCION = """Trabajas en desarrollo de negocio en Empresa, instituto \
tecnologico especializado en envase, transporte, logistica, sostenibilidad y \
seguridad alimentaria.

Empresa ha lanzado una campana. El mensaje, los datos tecnicos, las fechas y lo \
que se ofrece YA ESTAN DECIDIDOS y te los doy en el brief. Tu unico trabajo es \
escribir el correo para UNA empresa concreta, conectando el mensaje de la \
campana con lo que esa empresa hace.

ESTRUCTURA
1. Asunto: concreto, que se entienda de que va.
2. Saludo: "Buenos dias," y nada mas (no conoces su nombre).
3. Abre por el DISPARADOR de la campana, no por vosotros. Lo que ha pasado en \
el mundo que justifica escribir ahora.
4. El enlace con esta empresa: por que ese asunto le afecta a ELLA, dado lo que \
hace. Es la unica parte que escribes tu de verdad, y la mas importante.
5. Los puntos tecnicos del brief que le apliquen a esta empresa. No todos: los \
que le toquen.
6. Lo que se ofrece, segun el brief.
7. Cierre pidiendo disponibilidad, agradeciendo.
8. Firma.

REGLAS
- Entre 200 y 320 palabras.
- TUTEA. Es el tono de la casa: "te compartimos", "si estas revisando".
- Tono consultivo, no comercial. Ni venta ni entusiasmo.
- Los datos tecnicos, fechas, normas y siglas SOLO pueden salir del brief. No \
anadas ninguno por tu cuenta, ni aunque te parezca razonable.
- Lo que digas de la empresa solo puede salir de su web.
- NO le cuentes a la empresa lo que la empresa hace. Da por sabida su \
actividad y pasa directamente a la consecuencia. Nada de "vosotros fabricais \
X": eso ya lo saben.
- NUNCA digas que has leido su web, su pagina ni su descripcion.
- Lo que fabrica la empresa es SUYO. Nunca digas "nuestros" refiriendote a sus \
productos.
- No prometas resultados ni plazos propios. No inventes casos de exito.
- Sin corchetes ni marcadores por rellenar.

SI LA CAMPANA NO LE APLICA
El brief dice a quien no le aplica. Si esta empresa esta claramente en ese \
caso, NO escribas el correo. Responde solo:
NO APLICA: <una linea explicando por que>
Abstenerse cuando no encaja es parte del trabajo. Forzar el encaje hace mas \
dano que no escribir.

Devuelve SOLO el correo, empezando por "Asunto:"."""


EJEMPLO_ENTRADA = """EMPRESA A CONTACTAR
Nombre: PLASTICOS ALZIRA
Lo que dice su web: Fabricamos film y bolsa de polietileno para agricultura e \
industria. Disponemos de linea propia de extrusion y de impresion \
flexografica. Nuestro compromiso con el entorno nos ha llevado a incorporar \
material reciclado en parte de nuestra gama. Suministramos a envasadores de \
producto fresco de toda la Comunidad Valenciana.

FIRMA
Mireia Borras · Desarrollo de Negocio · Empresa"""

EJEMPLO_SALIDA = """Asunto: Reciclabilidad del film de polietileno ante los hitos de agosto de 2026

Buenos dias,

La Comision Europea ha publicado el documento guia del Reglamento PPWR, y con \
el la industria entra en una fase de preparacion decisiva de cara a los \
primeros hitos exigibles a partir de agosto de 2026.

Para un film de polietileno destinado a envasadores de producto fresco, el \
punto mas inmediato es el requisito de reciclabilidad segun los estandares \
EN 13430: determina que envases podran seguir en el mercado y cuales habra que \
rediseniar. La incorporacion de material reciclado en parte de la gama juega a \
favor, pero conviene poder acreditarla en los terminos que exige el reglamento. \
Y en la medida en que ese film acabe en contacto con alimento, entran tambien \
las restricciones de PFAS y metales pesados, ademas de la responsabilidad sobre \
las Declaraciones de Conformidad.

Desde Empresa hemos elaborado un informe tecnico de conclusiones sobre las \
novedades del documento guia, que te compartimos para que puedas valorar que \
te afecta y en que orden. Nuestro trabajo abarca desde el asesoramiento tecnico \
y la validacion del cumplimiento hasta el desarrollo de nuevas soluciones de \
envase.

Estas ultimas semanas estamos recibiendo bastantes peticiones en este sentido, \
por la urgencia de decidir a tiempo.

Quedo a la espera de conocer tu disponibilidad. Muchas gracias.

Un cordial saludo,

Mireia Borras
Desarrollo de Negocio · Empresa"""


def construir_contexto(empresa, web, firma):
    return f"""EMPRESA A CONTACTAR
Nombre: {empresa}
Lo que dice su web: {web[:MAX_CARACTERES]}

FIRMA
{firma}"""


def construir_mensajes(empresa, web, campana, firma, con_ejemplo=True):
    sistema = INSTRUCCION + "\n\n===== BRIEF DE LA CAMPANA =====\n" + campana["texto"]
    m = [{"role": "system", "content": sistema}]
    if con_ejemplo:
        m.append({"role": "user", "content": EJEMPLO_ENTRADA})
        m.append({"role": "assistant", "content": EJEMPLO_SALIDA})
    m.append({"role": "user", "content": construir_contexto(empresa, web, firma)})
    return m


# ==========================================================================
# Verificacion
# ==========================================================================

def verificar(correo, web, campana):
    """Comprueba el correo contra sus dos fuentes de evidencia.

    A diferencia de F5_A5_E19_generar_correos.py, aqui la evidencia tiene DOS partes y conviene
    separarlas: lo que viene del brief es comun a todos los correos, asi que no
    cuenta como personalizacion aunque este perfectamente fundamentado.
    """
    t_cor = terminos(correo)
    t_web = terminos(web)
    t_brief = terminos(campana["texto"])

    inventados = t_cor - (t_web | t_brief)
    fundamentacion = 1 - len(inventados) / max(len(t_cor), 1)

    # lo que procede de ESTA empresa y no del brief comun
    propios = (t_cor & t_web) - t_brief
    personalizacion = len(propios) / max(len(t_cor), 1)

    c = sin_acentos(correo)
    palabras = len(correo.split())
    return {
        "palabras": palabras,
        "cumple_longitud": 170 <= palabras <= 360,
        "fundamentacion": round(fundamentacion, 3),
        "personalizacion": round(personalizacion, 3),
        "terminos_no_respaldados": len(inventados),
        "tiene_saludo": bool(SALUDOS.search(c)) or "buenos dias" in c,
        "tiene_despedida": bool(DESPEDIDAS.search(c)),
        "agradece": bool(AGRADECE.search(c)),
        "tutea": bool(re.search(r"\bte\b|\btu\b|\btus\b|\bestas\b|\bpuedes\b", c)),
        "marcador_sin_rellenar": bool(TIC_MARCADOR.search(correo)),
        "se_delata_leyendo_web": bool(TIC_LECTURA.search(c)),
        "muestra_no_respaldados": ", ".join(sorted(inventados)[:8]),
    }


# ==========================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campana", default="C01")
    ap.add_argument("--campanas", default=None,
                    help="ruta del documento de campanas; por omision busca "
                         "12_CAMPANAS.docx y, si no esta, 12_CAMPANAS.md")
    ap.add_argument("--modelo", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--muestra", type=int, default=40)
    ap.add_argument("--lote", type=int, default=2)
    ap.add_argument("--temperatura", type=float, default=0.6)
    ap.add_argument("--firma", default="Mireia Borras · Desarrollo de Negocio · Empresa")
    ap.add_argument("--sin_ejemplo", action="store_true",
                    help="ablacion: sin el correo resuelto")
    ap.add_argument("--salida", default="a5_campana_C01.csv")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    campana = leer_campana(a.campana)

    print("=" * 70)
    print("A5 · CORREOS DE CAMPANA")
    print(f"     {VERSION_SCRIPT}")
    print(f"     campana: {campana['codigo']} · {campana['nombre']}")
    print(f"     ejemplo resuelto: {'NO (ablacion)' if a.sin_ejemplo else 'SI'}")
    print("=" * 70)
    if not torch.cuda.is_available():
        print("\n*** SIN GPU: ejecutalo en Colab ***")
        sys.exit(1)
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    # las mismas empresas que en E19, para poder comparar
    d = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                   for p in ["train", "val", "test"]], ignore_index=True)
    d = d[d.tiene_texto.fillna(False)].sample(n=300, random_state=42).reset_index(drop=True)
    sel = d.head(a.muestra)
    print(f"\nEmpresas: {len(sel)}  (misma muestra que E19)")

    tok = AutoTokenizer.from_pretrained(a.modelo)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    # el prompt lleva el brief entero: hay que comprobar que cabe (error X4)
    prueba = tok.apply_chat_template(
        construir_mensajes("PRUEBA", "x" * MAX_CARACTERES, campana, a.firma,
                           not a.sin_ejemplo),
        tokenize=False, add_generation_prompt=True)
    n_prompt = len(tok(prueba).input_ids)
    MAX_ENTRADA = 6144
    print(f"prompt: {n_prompt} tokens (limite {MAX_ENTRADA})")
    if n_prompt > MAX_ENTRADA:
        sys.exit("El prompt excede el limite y se truncaria por el final, que es "
                 "donde va la empresa. Acorta el brief o MAX_CARACTERES.")

    modelo = AutoModelForCausalLM.from_pretrained(
        a.modelo, device_map="auto", torch_dtype=torch.float16,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True))
    modelo.eval()

    filas = []
    for k in range(0, len(sel), a.lote):
        lote = sel.iloc[k:k + a.lote]
        textos = [tok.apply_chat_template(
            construir_mensajes(r.empresa_clave, r.web_text, campana, a.firma,
                               not a.sin_ejemplo),
            tokenize=False, add_generation_prompt=True) for r in lote.itertuples()]
        ent = tok(textos, return_tensors="pt", padding=True,
                  truncation=True, max_length=MAX_ENTRADA).to(modelo.device)
        with torch.no_grad():
            out = modelo.generate(**ent, max_new_tokens=700, do_sample=True,
                                  temperature=a.temperatura, top_p=0.9,
                                  repetition_penalty=1.05,
                                  pad_token_id=tok.pad_token_id)
        for r, o in zip(lote.itertuples(), out):
            correo = tok.decode(o[ent.input_ids.shape[1]:],
                                skip_special_tokens=True).strip()
            abstiene = correo.upper().startswith(MARCA_ABSTENCION)
            if abstiene:
                v = {"palabras": len(correo.split()), "cumple_longitud": None,
                     "fundamentacion": None, "personalizacion": None,
                     "terminos_no_respaldados": None, "tiene_saludo": None,
                     "tiene_despedida": None, "agradece": None, "tutea": None,
                     "marcador_sin_rellenar": None,
                     "se_delata_leyendo_web": None, "muestra_no_respaldados": ""}
            else:
                v = verificar(correo, r.web_text, campana)
            filas.append({"empresa_clave": r.empresa_clave, "sector": r.sector,
                          "campana": campana["codigo"], "se_abstiene": abstiene,
                          "correo": correo, **v})
        print(f"   {len(filas)}/{len(sel)}")

    e = pd.DataFrame(filas)
    esc = e[~e.se_abstiene]

    print("\n" + "=" * 70)
    print("EVALUACION")
    print("=" * 70)
    print(f"   correos escritos           : {len(esc)}/{len(e)}")
    print(f"   se abstiene (no aplica)    : {e.se_abstiene.mean()*100:.1f}%")
    if e.se_abstiene.any():
        print("      " + " · ".join(e[e.se_abstiene].sector.astype(str).head(6)))

    if len(esc) == 0:
        e.to_csv(SALIDA / a.salida, index=False, encoding="utf-8")
        print("\n   Se ha abstenido en todos los casos. Revisa el brief.")
        return

    print(f"\n   longitud media             : {esc.palabras.mean():.0f} palabras")
    print(f"   dentro de 170-360          : {esc.cumple_longitud.mean()*100:.1f}%")

    print(f"\n   ESTRUCTURA Y TONO")
    for col, etiqueta in [("tiene_saludo", "saludo"), ("tiene_despedida", "despedida"),
                          ("agradece", "agradece"), ("tutea", "tutea")]:
        print(f"      {etiqueta:<22} : {esc[col].mean()*100:5.1f}%")

    print(f"\n   TICS  <- deberian ser 0")
    print(f"      marcador sin rellenar  : {esc.marcador_sin_rellenar.mean()*100:5.1f}%")
    print(f"      se delata leyendo web  : {esc.se_delata_leyendo_web.mean()*100:5.1f}%")

    print(f"\n   FUNDAMENTACION (web + brief)")
    print(f"      media                  : {esc.fundamentacion.mean()*100:5.1f}%")
    print(f"      OJO: sube respecto a E19 porque el brief es evidencia nueva.")
    print(f"      Compara la distancia al suelo, no el porcentaje.")

    print(f"\n   PERSONALIZACION (parte que viene de la web de ESA empresa)")
    print(f"      correos generados      : {esc.personalizacion.mean()*100:5.1f}%")

    # El punto de referencia no se inventa: es el correo generico real que
    # Empresa lanza hoy, evaluado contra las webs de estas mismas empresas.
    # Fijar un umbral a ojo fue el error X9; aqui se mide el suelo.
    generico = RAIZ / "datos" / "00_bruto" / f"correo_generico_{a.campana}.txt"
    if generico.exists():
        txt = re.sub(r"\{\{[^}]*\}\}", "", generico.read_text(encoding="utf-8"))
        t_gen = terminos(txt)
        t_brief = terminos(campana["texto"])
        base = [len((t_gen & terminos(w)) - t_brief) / max(len(t_gen), 1)
                for w in sel.web_text.fillna("")]
        base = float(np.mean(base))
        print(f"      correo generico actual : {base*100:5.1f}%   <- el suelo real")
        print(f"      diferencia             : {(esc.personalizacion.mean()-base)*100:+5.1f}"
              f" puntos")
        print(f"      (el generico no es cero: comparte lexico con cualquier web")
        print(f"       por azar, y eso hay que descontarlo)")
    else:
        print(f"      (falta {generico.name}: sin el no hay punto de referencia)")

    # redundancia: ¿son todos el mismo correo con otro nombre?
    try:
        from sentence_transformers import SentenceTransformer
        emb = SentenceTransformer("intfloat/multilingual-e5-small")
        V = emb.encode(["query: " + c for c in esc.correo],
                       normalize_embeddings=True, batch_size=16)
        S = V @ V.T
        iu = np.triu_indices(len(V), k=1)
        print(f"\n   REDUNDANCIA ENTRE CORREOS")
        print(f"      parecido medio entre pares : {S[iu].mean():.3f}")
        print(f"      (el correo generico actual tiene 1,000 por definicion:")
        print(f"       es literalmente el mismo para todas las empresas)")
        print(f"      maximo entre dos correos   : {S[iu].max():.3f}")
    except ImportError:
        print("\n   (sin sentence-transformers no se calcula la redundancia)")

    e.to_csv(SALIDA / a.salida, index=False, encoding="utf-8")
    print(f"\n   Guardado: {a.salida}  (lee diez a mano)")


if __name__ == "__main__":
    main()
