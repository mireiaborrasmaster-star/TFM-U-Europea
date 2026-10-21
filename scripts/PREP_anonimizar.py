"""
ANONIMIZACION DE DATOS PARA EL TFM
===================================

Convierte los ficheros de 'datos/00_bruto/' en versiones anonimizadas en
'datos/01_limpio/', conservando TODO lo que los modelos necesitan y eliminando
u ocultando lo que identifica a personas.

Principio: anonimizar NO es borrar. Hay cuatro tratamientos:

    CONSERVAR    Se deja tal cual. Sector, tamaño, fechas, importes, etapas.
                 No identifican a nadie y son las variables del modelo.

    SEUDONIMIZAR El valor se sustituye por un codigo estable (ej. "A7F3").
                 El mismo nombre da siempre el mismo codigo, en todas las
                 tablas, asi que se puede agrupar y cruzar igual que antes.
                 El modelo no pierde absolutamente nada.

    LIMPIAR      Para texto libre: quita nombres, emails, telefonos, NIFs e
                 IBANs, y conserva el resto del contenido.

    ELIMINAR     La columna desaparece. Solo para datos personales que ningun
                 modelo usa: nombre de contacto, email, telefono.

USO EN DOS PASOS
----------------
    # 1) Inspecciona y propone un tratamiento por columna. NO modifica nada.
    python PREP_anonimizar.py --revisar

    Genera 'datos/config_anonimizacion.json' y un informe por pantalla.
    REVISA ESE FICHERO y corrige lo que no te cuadre.

    # 2) Aplica la configuracion
    python PREP_anonimizar.py --aplicar

IMPORTANTE
----------
  · La tabla que traduce codigo -> nombre real se guarda en
    'datos/_mapeo_privado/'. NO la compartas ni la subas a ningun sitio.
    Sirve para que TU puedas volver al nombre real cuando lo necesites.
  · Los ficheros de 00_bruto/ nunca se modifican.
  · Todo queda registrado en 'datos/01_limpio/registro_anonimizacion.txt',
    que es material directo para el capitulo de proteccion de datos.
"""

import argparse
import hashlib
import json
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
PRIVADO = RAIZ / "datos" / "_mapeo_privado"
CONFIG = RAIZ / "datos" / "config_anonimizacion.json"

CONSERVAR, SEUDONIMIZAR, LIMPIAR, ELIMINAR = (
    "CONSERVAR", "SEUDONIMIZAR", "LIMPIAR", "ELIMINAR")


# ==========================================================================
# Deteccion de datos personales dentro de texto
# ==========================================================================

RE_EMAIL = re.compile(r"[\w\.\-\+]+@[\w\-]+\.[\w\.\-]+")
RE_TELEFONO = re.compile(r"(?:(?:\+|00)\d{1,3}[\s\.\-]?)?(?:\d[\s\.\-]?){9,}")
RE_NIF = re.compile(r"\b[A-HJ-NP-SUVW]\d{7}[0-9A-J]\b|\b\d{8}[A-HJ-NP-TV-Z]\b",
                    re.IGNORECASE)
RE_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,7}\b")
RE_URL = re.compile(r"https?://\S+|www\.\S+")

# Nombres de persona: se detectan por el patron "Tratamiento + Nombre Apellido"
RE_NOMBRE = re.compile(
    r"\b(?:Sr|Sra|Sres|D|Dn|Dña|Don|Doña)\.?\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
    r"(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2}")


def limpiar_texto(valor):
    """Quita datos personales de un texto libre, conservando el contenido util."""
    if pd.isna(valor):
        return valor
    t = str(valor)
    t = RE_EMAIL.sub("[EMAIL]", t)
    t = RE_IBAN.sub("[IBAN]", t)
    t = RE_NIF.sub("[NIF]", t)
    t = RE_NOMBRE.sub("[PERSONA]", t)
    t = RE_URL.sub("[URL]", t)
    t = RE_TELEFONO.sub("[TELEFONO]", t)
    return re.sub(r"\s+", " ", t).strip()


# ==========================================================================
# Seudonimizacion estable
# ==========================================================================

def cargar_sal():
    """La sal hace que los codigos no se puedan revertir por fuerza bruta.
    Se genera una vez y se reutiliza siempre: si cambia, los codigos cambian
    y se pierde la capacidad de cruzar tablas."""
    PRIVADO.mkdir(parents=True, exist_ok=True)
    f = PRIVADO / "sal.txt"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    sal = secrets.token_hex(16)
    f.write_text(sal, encoding="utf-8")
    print(f"  Generada sal nueva en {f.name}. NO la borres ni la compartas.")
    return sal


def normalizar_nombre(valor):
    """Para que 'ACME S.L.' y 'Acme SL' den el mismo codigo."""
    t = str(valor).strip().upper()
    t = re.sub(r"[^A-Z0-9ÁÉÍÓÚÑ ]", " ", t)
    t = re.sub(r"\b(SL|SLU|SA|SAU|SC|SCCL|SLL|COOP|CB)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def seudonimizar(serie, sal, prefijo, memoria):
    """Sustituye cada valor por un codigo corto y estable."""
    def codificar(v):
        if pd.isna(v) or str(v).strip() == "":
            return None
        clave = normalizar_nombre(v)
        if clave not in memoria:
            h = hashlib.sha256((sal + clave).encode("utf-8")).hexdigest()
            memoria[clave] = f"{prefijo}{h[:8].upper()}"
        return memoria[clave]
    return serie.map(codificar)


# ==========================================================================
# PASO 1 · Revisar y proponer
# ==========================================================================

PATRONES = [
    # --- EXCEPCIONES PRIMERO: nombres de columna que enganan ---
    # Se comprueban antes que las reglas generales porque contienen palabras
    # que activarian una regla equivocada.
    (r"raz[oó]n\s*social\s*:\s*(ciudad|poblaci|localidad|municipio)",
                                         CONSERVAR,    "es la CIUDAD, no la razon social"),
    (r"personalidad\s*jur[ií]dica",      CONSERVAR,    "SL/SA/cooperativa: no es dato personal"),
    (r"^\(no modificar\).*fecha",        CONSERVAR,    "es una fecha, aunque el CRM la marque como no modificable"),
    (r"^\(no modificar\).*(suma|comprobaci|checksum)",
                                         ELIMINAR,     "suma de control interna: no aporta nada"),
    (r"^\(no modificar\)",              SEUDONIMIZAR, "identificador interno del CRM"),

    # (regex sobre el nombre de columna, tratamiento, motivo)
    (r"email|correo|e_?mail",            ELIMINAR,     "dato personal directo"),
    (r"tel[eé]fono|m[oó]vil|^fax",       ELIMINAR,     "dato personal directo"),
    (r"^dni|^nie|pasaporte",             ELIMINAR,     "dato personal directo"),
    (r"^contacto|persona|interlocutor|responsable",
                                         ELIMINAR,     "nombre de persona fisica"),
    (r"iban|cuenta_?banc|tarjeta",       ELIMINAR,     "dato financiero"),
    (r"importe|precio|tarifa|facturaci|probabilidad|margen|coste",
                                         ELIMINAR,     "informacion comercial sensible (decision D13)"),
    (r"^direccion|domicilio|^calle",     ELIMINAR,     "no aporta al modelo"),

    # --- identificadores de cuenta (clave del cruce entre ficheros) ---
    (r"n[uú]mero\s*de\s*cuenta|^id[\s_]*cuenta|c[oó]digo\s*de\s*cuenta",
                                         SEUDONIMIZAR, "ID de cuenta: clave del cruce"),
    (r"nombre\s*(de\s*)?(cuenta|empresa|cliente)|raz[oó]n\s*social|"
     r"^empresa$|^cuenta$|^alias$",
                                         SEUDONIMIZAR, "identifica la empresa; solo se necesita para agrupar"),
    (r"^cif|^nif|^vat",                  SEUDONIMIZAR, "identificador fiscal"),
    (r"propietario|comercial|owner|usuario|asignad|vendedor|^autor",
                                         SEUDONIMIZAR, "hay que distinguirlos, no identificarlos"),
    (r"n[ºo°]?\s*oportunidad|n[ºo°]?\s*oferta|^id_|_id$",
                                         SEUDONIMIZAR, "identificador de registro"),
    (r"sitio\s*web|^web$|^url$",         SEUDONIMIZAR, "la web identifica a la empresa"),

    # --- texto libre: se conserva el contenido, se quitan los datos personales ---
    (r"^tema$|^nombre$|descripci[oó]n|observaci|comentari|^nota|detalle|"
     r"asunto|consulta|necesidad",
                                         LIMPIAR,      "texto libre: puede contener datos personales"),

    # --- variables del modelo ---
    (r"sector|subsector|[aá]rea|l[ií]nea|tama[nñ]o|provincia|ciudad|pa[ií]s|"
     r"fecha|importe|estado|etapa|tipo|tipolog|servicio|motivo|origen|duracion|"
     r"cantidad|numero\s*de\s*(version|horas)|^n_|conteo|probabilidad|"
     r"atractividad|asociado|^cliente$|personalidad|centro\s*de\s*coste|horas",
                                         CONSERVAR,    "variable del modelo, no identifica a nadie"),
]


def proponer(col, serie):
    """Propone tratamiento a partir del nombre de la columna y, si no hay
    coincidencia, del contenido."""
    c = col.lower().strip()
    for patron, trat, motivo in PATRONES:
        if re.search(patron, c):
            return trat, motivo

    # Sin coincidencia por nombre: se mira el contenido
    muestra = serie.dropna().astype(str).head(200)
    if len(muestra) == 0:
        return CONSERVAR, "columna vacia"
    if muestra.str.contains(RE_EMAIL).any():
        return ELIMINAR, "el contenido parece contener emails"
    if muestra.str.len().mean() > 120:
        return LIMPIAR, "texto largo: podria contener datos personales"
    if pd.api.types.is_numeric_dtype(serie) or pd.api.types.is_datetime64_any_dtype(serie):
        return CONSERVAR, "numerico o fecha"
    n_unicos = serie.nunique(dropna=True)
    if n_unicos > 0.5 * len(serie) and n_unicos > 50:
        return SEUDONIMIZAR, f"muy variable ({n_unicos} valores distintos): parece un identificador"
    return CONSERVAR, f"categorica con {n_unicos} valores distintos"


def revisar():
    if not BRUTO.exists() or not any(BRUTO.iterdir()):
        sys.exit(f"No hay ficheros en {BRUTO}\n"
                 f"Copia ahi los exports del CRM y vuelve a ejecutar.")

    config = {}
    print("=" * 74)
    print("REVISION DE COLUMNAS")
    print("=" * 74)
    print("\nRevisa la propuesta. Si algo no te cuadra, edita")
    print(f"{CONFIG.name} antes de ejecutar --aplicar.\n")

    for f in sorted(BRUTO.iterdir()):
        if f.suffix.lower() not in (".csv", ".xlsx", ".xls"):
            continue
        try:
            df = (pd.read_excel(f) if f.suffix.lower() in (".xlsx", ".xls")
                  else pd.read_csv(f, sep=None, engine="python", encoding="utf-8"))
        except Exception as e:
            print(f"  [!] No se pudo leer {f.name}: {e}")
            continue

        print("-" * 74)
        print(f"FICHERO: {f.name}   ({len(df)} filas, {len(df.columns)} columnas)")
        print("-" * 74)
        cols = {}
        for col in df.columns:
            trat, motivo = proponer(col, df[col])
            cols[col] = {"tratamiento": trat, "motivo": motivo}
            icono = {CONSERVAR: "  ", SEUDONIMIZAR: "~ ",
                     LIMPIAR: "* ", ELIMINAR: "X "}[trat]
            print(f" {icono}{str(col)[:34]:<34} {trat:<13} {motivo}")
        config[f.name] = cols

    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    print("\n" + "=" * 74)
    print(f"Configuracion guardada en: {CONFIG}")
    print("=" * 74)
    print("""
LEYENDA
     (nada)  CONSERVAR     se deja tal cual
     ~       SEUDONIMIZAR  se sustituye por un codigo estable
     *       LIMPIAR       se quitan datos personales del texto
     X       ELIMINAR      la columna desaparece

SIGUIENTE PASO
  1. Abre el JSON y corrige los tratamientos que no te convenzan.
  2. Ejecuta:  python PREP_anonimizar.py --aplicar
""")


# ==========================================================================
# PASO 2 · Aplicar
# ==========================================================================

def aplicar():
    if not CONFIG.exists():
        sys.exit("Falta la configuracion. Ejecuta antes: python PREP_anonimizar.py --revisar")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    sal = cargar_sal()
    LIMPIO.mkdir(parents=True, exist_ok=True)

    # Memoria compartida entre ficheros: garantiza que la misma empresa
    # recibe el mismo codigo en todas las tablas.
    memoria_path = PRIVADO / "mapeo.json"
    memoria = (json.loads(memoria_path.read_text(encoding="utf-8"))
               if memoria_path.exists() else {})

    registro = [
        "REGISTRO DE ANONIMIZACION",
        "=" * 74,
        f"Fecha: {datetime.now():%Y-%m-%d %H:%M}",
        "",
    ]

    for nombre_fichero, cols in config.items():
        f = BRUTO / nombre_fichero
        if not f.exists():
            print(f"  [!] No encontrado: {nombre_fichero}")
            continue
        df = (pd.read_excel(f) if f.suffix.lower() in (".xlsx", ".xls")
              else pd.read_csv(f, sep=None, engine="python", encoding="utf-8"))

        print(f"\nProcesando {nombre_fichero} ({len(df)} filas)")
        registro += [f"FICHERO: {nombre_fichero} ({len(df)} filas)", "-" * 74]

        eliminadas, seudo, limpiadas = [], [], []
        for col, cfg in cols.items():
            if col not in df.columns:
                continue
            t = cfg["tratamiento"]
            if t == ELIMINAR:
                df = df.drop(columns=[col]); eliminadas.append(col)
            elif t == SEUDONIMIZAR:
                prefijo = "EMP_" if re.search(
                    r"empresa|cuenta|cliente|social|cif|alias|url|web", col.lower()) else "ID_"
                df[col] = seudonimizar(df[col], sal, prefijo, memoria)
                seudo.append(col)
            elif t == LIMPIAR:
                df[col] = df[col].map(limpiar_texto); limpiadas.append(col)

        salida = LIMPIO / (Path(nombre_fichero).stem + "_anon.csv")
        df.to_csv(salida, index=False, sep=";", encoding="utf-8")
        print(f"  -> {salida.name}  ({len(df)} filas, {len(df.columns)} columnas)")
        print(f"     eliminadas: {len(eliminadas)} | seudonimizadas: {len(seudo)} "
              f"| texto limpiado: {len(limpiadas)}")

        registro += [
            f"  Columnas eliminadas    ({len(eliminadas)}): {', '.join(eliminadas) or '-'}",
            f"  Columnas seudonimizadas({len(seudo)}): {', '.join(seudo) or '-'}",
            f"  Texto libre limpiado   ({len(limpiadas)}): {', '.join(limpiadas) or '-'}",
            f"  Columnas conservadas   ({len(df.columns) - len(seudo) - len(limpiadas)})",
            f"  Salida: {salida.name}", "",
        ]

    memoria_path.write_text(json.dumps(memoria, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    registro += [
        "=" * 74,
        "METODO",
        "  Seudonimizacion: SHA-256 con sal aleatoria de 128 bits, truncado a 8",
        "  caracteres. El mismo valor produce siempre el mismo codigo, lo que",
        "  permite cruzar tablas y agrupar por cliente sin revelar identidades.",
        "  La sal y la tabla de correspondencia se guardan separadas, fuera de",
        "  la carpeta de trabajo, y no se comparten.",
        "",
        "  Texto libre: eliminacion por expresiones regulares de emails,",
        "  telefonos, NIF/DNI, IBAN, URLs y nombres de persona precedidos de",
        "  tratamiento (Sr., D., Dña.), sustituidos por marcadores genericos.",
        "",
        "  Se conservan las variables sin capacidad identificativa que",
        "  constituyen la entrada de los modelos: sector, tamaño, provincia,",
        "  fechas, importes, etapas y metricas de actividad.",
        "",
        "LIMITACION CONOCIDA",
        "  La deteccion de nombres de persona en texto libre por patrones no es",
        "  exhaustiva. Se recomienda revision manual de una muestra del texto",
        "  libre antes de compartir los ficheros anonimizados.",
    ]
    (LIMPIO / "registro_anonimizacion.txt").write_text(
        "\n".join(registro), encoding="utf-8")

    print("\n" + "=" * 74)
    print(f"Listo. Ficheros anonimizados en: {LIMPIO}")
    print(f"Tabla de correspondencia (PRIVADA) en: {PRIVADO}")
    print(f"Registro para la memoria: {LIMPIO / 'registro_anonimizacion.txt'}")
    print("=" * 74)
    print("\nRECOMENDADO: abre un fichero *_anon.csv y comprueba que no queda")
    print("nada identificativo antes de seguir.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Anonimizacion de datos del TFM")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--revisar", action="store_true",
                   help="inspecciona y propone tratamiento por columna")
    g.add_argument("--aplicar", action="store_true",
                   help="aplica la configuracion revisada")
    a = ap.parse_args()
    revisar() if a.revisar else aplicar()
