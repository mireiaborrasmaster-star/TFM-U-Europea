"""
A5 · GENERACION DE CORREOS DE CONTACTO
=======================================
Escribe el primer correo a una empresa, conectando lo que Empresa ofrece con lo
que la empresa hace segun su propia web.

VERSION 2 · 28-09-2026 · estructura de correo y ejemplos resueltos

QUE CAMBIA RESPECTO A LA v1, Y POR QUE
--------------------------------------
La v1 cumplia todas las restricciones medidas y aun asi los correos no se
parecian a lo que escribe una persona. El diagnostico, leyendolos:

  1. EL PROMPT PEDIA UN TEXTO, NO UN CORREO. Decia "maximo 120 palabras" y
     "sin adjetivos comerciales vacios", y el modelo optimizo contra eso
     eliminando saludo, despedida y agradecimiento. Las convenciones sociales
     del correo no son relleno: son lo que hace que un desconocido lo lea.

  2. NO HABIA NINGUN EJEMPLO. Se describia el resultado deseado con reglas
     abstractas. Un modelo de 7B necesita ver el formato, no que se lo
     definan. Es la diferencia entre zero-shot y few-shot, ya medida en A2.

  3. NO HABIA HUECO PARA LA FIRMA, asi que el modelo improvisaba "[Tu Nombre]"
     en el 7,5% de los casos.

  4. NADIE LE PROHIBIO DELATARSE. En el 15% de los correos escribia cosas como
     "leyendo su descripcion, me llamo la atencion", que revela que quien
     escribe ha mirado la web en lugar de conocer a la empresa.

La v2 corrige los cuatro: da la estructura por partes, dos ejemplos resueltos,
los datos de la firma, y prohibiciones explicitas de los tics observados.

QUE SE EVALUA, Y QUE NO
-----------------------
No se puede medir "¿es un buen correo?": eso es subjetivo y exigiria que
alguien leyera cientos. Lo que SI se puede medir:

  FUNDAMENTACION  ¿Lo que el correo afirma sobre la empresa aparece en su web,
                  o se lo ha inventado el modelo?
  SERVICIO REAL   ¿Menciona un servicio que Empresa ofrece, o promete algo que
                  no existe?
  ESTRUCTURA      ¿Tiene saludo, cierre y firma, o es un parrafo suelto?
  TICS            ¿Cae en los defectos observados en la v1?

IMPORTANTE SOBRE LA FUNDAMENTACION
----------------------------------
Al anadir saludo y despedida se incorpora vocabulario de cortesia que no
aparece en ninguna web, de modo que la fundamentacion BAJARA mecanicamente.
Eso no significa que el correo se invente mas cosas.

Por eso la cifra bruta no se interpreta sola: hay que relanzar
F5_A5_E19_control_fundamentacion.py, que recalcula el suelo de la metrica por
permutacion. Lo que hay que comparar entre v1 y v2 es la DISTANCIA al suelo,
no el porcentaje. Ver X9 en la bitacora.

Uso en Colab (necesita GPU):
    !pip install -q transformers accelerate bitsandbytes sentence-transformers
    !python scripts/F5_A5_E19_generar_correos.py --muestra 40
"""

import argparse
import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v2 · 28-09-2026 · estructura de correo y ejemplos resueltos"

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent))
from F5_A5_E17_emparejar_lexico import leer_catalogo, sin_acentos  # noqa: E402
from F5_A5_E18_emparejar_semantico import texto_servicio, MAX_CARACTERES  # noqa: E402


# ==========================================================================
# El prompt
# ==========================================================================

INSTRUCCION = """Eres responsable de desarrollo de negocio en Empresa, instituto \
tecnologico especializado en envase, transporte, logistica, sostenibilidad y \
seguridad alimentaria.

Escribes el PRIMER correo a una empresa con la que nunca se ha hablado. Es un \
correo profesional normal, del tipo que una persona escribe y otra persona lee \
sin extranarse.

ESTRUCTURA, EN ESTE ORDEN
1. Asunto: concreto y sin mayusculas de reclamo. Que se entienda de que va.
2. Saludo formal, tratando de usted.
3. Una linea de cortesia inicial.
4. Presentacion breve: quien escribe y desde donde.
5. El motivo: UNA cosa concreta que hace la empresa, y por que eso conecta con \
el servicio que se propone. Esta es la parte importante.
6. Una pregunta concreta o una propuesta de conversacion breve.
7. Despedida agradeciendo la atencion y ofreciendo quedar a su disposicion.
8. Firma.

REGLAS
- Entre 130 y 180 palabras en total.
- Trata de usted en todo el correo.
- No afirmes NADA que no aparezca en la informacion que te doy. Si no sabes su \
tamano, su facturacion ni sus problemas, no los menciones.
- NUNCA digas que has leido su web, su pagina ni su descripcion. Nada de \
"segun su web", "leyendo su descripcion" ni "he visto en su pagina". Menciona \
lo que hacen con naturalidad, como quien ya lo sabe.
- Los productos de la empresa son SUYOS, no nuestros. Nunca digas "nuestros" \
refiriendote a lo que fabrica el cliente.
- No prometas resultados, plazos ni ahorros. No inventes casos de exito.
- No uses corchetes ni marcadores por rellenar: la firma va completa.
- Escribe en castellano correcto, sin calcos del ingles.

Devuelve SOLO el correo, empezando por "Asunto:"."""


# -- Ejemplos resueltos ----------------------------------------------------
# Se le ensena el formato en lugar de describirselo. Las dos empresas son
# inventadas a proposito: no deben salir datos reales de Empresa en el prompt, y
# ademas asi se comprueba que el modelo copia la ESTRUCTURA y no el contenido.

EJEMPLOS = [
    (
        """EMPRESA A CONTACTAR
Nombre: CONSERVAS DEL MEDITERRANEO
Lo que dice su web: Elaboramos conservas vegetales y platos preparados en \
nuestra planta de Murcia. Trabajamos con alcachofa, pimiento y tomate de \
temporada. Exportamos a Francia, Alemania y Reino Unido.

SERVICIO QUE PROPONEMOS
Vida util y estabilidad del producto
Determinar cuanto dura un producto en condiciones reales y como influye el \
envase. Permite fijar la fecha de consumo preferente con respaldo tecnico.
A quien le sirve: Industria alimentaria y de bebidas, y quien quiera entrar en \
mercados de exportacion con trayectos largos.

FIRMA
Mireia Borras · Desarrollo de Negocio · Empresa""",
        """Asunto: Respaldo tecnico de la vida util para sus mercados de exportacion

Estimados senores:

Espero que se encuentren bien.

Me pongo en contacto con ustedes desde Empresa, instituto tecnologico centrado \
en envase, logistica y seguridad alimentaria.

Trabajan conservas vegetales y platos preparados con producto de temporada, y \
los envian a Francia, Alemania y Reino Unido. En los destinos de exportacion, \
la fecha de consumo preferente suele revisarse con mas detalle que en el \
mercado nacional, y conviene poder sostenerla con un estudio propio. Nosotros \
determinamos la vida util en condiciones reales y medimos como influye el \
envase en ella.

¿Seria posible mantener una conversacion breve para ver si encaja con lo que \
tienen ahora entre manos?

Les agradezco su atencion y quedo a su disposicion para lo que necesiten.

Un cordial saludo,

Mireia Borras
Desarrollo de Negocio · Empresa""",
    ),
    (
        """EMPRESA A CONTACTAR
Nombre: PLASTICOS ALZIRA
Lo que dice su web: Fabricamos film y bolsa de polietileno para agricultura e \
industria. Disponemos de linea propia de extrusion y de impresion \
flexografica. Nuestro compromiso con el entorno nos ha llevado a incorporar \
material reciclado en parte de nuestra gama.

SERVICIO QUE PROPONEMOS
Reciclabilidad y economia circular
Evaluar si un envase es realmente reciclable en las plantas existentes y que \
habria que cambiar para que lo fuera. Incluye el encaje con la normativa \
europea de envases.
A quien le sirve: Fabricantes de envase y marcas que deban acreditar \
reciclabilidad ante sus clientes o ante la Administracion.

FIRMA
Mireia Borras · Desarrollo de Negocio · Empresa""",
        """Asunto: Acreditacion de reciclabilidad del film de polietileno

Estimados senores:

Confio en que se encuentren bien.

Les escribo desde Empresa, instituto tecnologico especializado en envase y \
sostenibilidad.

Fabrican film y bolsa de polietileno con linea propia de extrusion, y han \
empezado a incorporar material reciclado en parte de su gama. Ese paso suele \
venir acompanado de peticiones de sus clientes para acreditar que el envase es \
reciclable de verdad en las plantas que hay hoy en funcionamiento. Es \
precisamente lo que evaluamos: si lo es, y que tendria que cambiar en caso \
contrario.

¿Les vendria bien una conversacion de veinte minutos para ver si les resulta \
util?

Muchas gracias por su atencion. Quedo a su disposicion para ampliar cualquier \
punto.

Un cordial saludo,

Mireia Borras
Desarrollo de Negocio · Empresa""",
    ),
]


def construir_contexto(empresa, web, servicio, firma):
    return f"""EMPRESA A CONTACTAR
Nombre: {empresa}
Lo que dice su web: {web[:MAX_CARACTERES]}

SERVICIO QUE PROPONEMOS
{servicio['nombre']}
{servicio['resuelve']}
A quien le sirve: {servicio['para_quien']}

FIRMA
{firma}"""


def construir_mensajes(empresa, web, servicio, firma, con_ejemplos=True):
    """Ejemplos resueltos como turnos de conversacion.

    Es la forma correcta de dar few-shot a un modelo de chat: el modelo ve dos
    intercambios completos antes del suyo, en lugar de una descripcion del
    formato dentro de las instrucciones."""
    m = [{"role": "system", "content": INSTRUCCION}]
    if con_ejemplos:
        for entrada, salida in EJEMPLOS:
            m.append({"role": "user", "content": entrada})
            m.append({"role": "assistant", "content": salida})
    m.append({"role": "user",
              "content": construir_contexto(empresa, web, servicio, firma)})
    return m


# ==========================================================================
# Verificacion
# ==========================================================================

VACIAS = {"que", "de", "la", "el", "los", "las", "una", "uno", "para", "con",
          "por", "del", "las", "sus", "este", "esta", "como", "mas", "sobre",
          "entre", "desde", "hasta", "pero", "todo", "cada", "muy", "ser",
          "son", "han", "hay", "les", "nos", "vuestro", "vuestra", "empresa",
          "empresa", "correo", "asunto", "cuerpo", "saludo", "hola", "gracias"}


def raiz(palabra):
    """Recorta la palabra a su raiz aproximada para que las formas conjugadas
    cuenten como la misma.

    Sin esto, un correo que dice "elaborais" se considera no respaldado aunque
    la web diga "elabora". Es el mismo problema de formas morfologicas que
    invalidaba el emparejamiento lexico (E17): comparar cadenas exactas cuando
    lo que importa es la palabra."""
    p = palabra
    for suf in ("mientos", "aciones", "amiento", "ciones", "mente", "ando",
                "endo", "imos", "amos", "eis", "ais", "ado", "ido", "ar",
                "er", "ir", "es", "as", "os", "a", "o", "s"):
        if len(p) - len(suf) >= 5 and p.endswith(suf):
            return p[:-len(suf)]
    return p


def terminos(texto, minimo=5):
    t = sin_acentos(texto)
    return {raiz(w) for w in re.findall(r"[a-z]{%d,}" % minimo, t)
            if w not in VACIAS}


# Tics observados en la v1, ahora medidos uno a uno
TIC_LECTURA = re.compile(
    r"(su|vuestra)\s+(web|pagina|sitio|descripcion)|segun\s+su\s+web|"
    r"he\s+(visto|leido)|leyendo\s+su|en\s+su\s+pagina")
TIC_MARCADOR = re.compile(r"\[[^\]]{2,40}\]")
SALUDOS = re.compile(r"estimad|buenos dias|buenas tardes|senor|apreciad")
DESPEDIDAS = re.compile(r"cordial|atentamente|un saludo|saludos|"
                        r"quedo a su disposicion|quedamos a su disposicion")
# "agradec" no vale: "agradezco" cambia la raiz. Se corta antes.
AGRADECE = re.compile(r"graci|agrad")


def verificar(correo, web, servicio, catalogo):
    """Comprueba si el correo se sostiene sobre la evidencia dada y si tiene
    la estructura de un correo de verdad."""
    t_correo = terminos(correo)
    t_evidencia = terminos(web) | terminos(texto_servicio(servicio))

    # terminos del correo que no aparecen ni en la web ni en el servicio
    inventados = t_correo - t_evidencia
    fundamentacion = 1 - len(inventados) / max(len(t_correo), 1)

    # ¿menciona algun servicio que Empresa no ofrece?
    otros = {sin_acentos(s["nombre"]) for s in catalogo
             if s["codigo"] != servicio["codigo"]}
    c = sin_acentos(correo)
    ajenos = [o for o in otros if o in c]

    palabras = len(correo.split())
    return {
        "palabras": palabras,
        "cumple_longitud": 110 <= palabras <= 200,
        "fundamentacion": round(fundamentacion, 3),
        "terminos_no_respaldados": len(inventados),
        "menciona_servicio_ajeno": len(ajenos) > 0,
        "tiene_pregunta": "?" in correo,
        # estructura
        "tiene_saludo": bool(SALUDOS.search(c)),
        "tiene_despedida": bool(DESPEDIDAS.search(c)),
        "agradece": bool(AGRADECE.search(c)),
        # tics de la v1
        "marcador_sin_rellenar": bool(TIC_MARCADOR.search(correo)),
        "se_delata_leyendo_web": bool(TIC_LECTURA.search(c)),
        "muestra_no_respaldados": ", ".join(sorted(inventados)[:8]),
    }


# ==========================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--muestra", type=int, default=40)
    ap.add_argument("--lote", type=int, default=4)
    ap.add_argument("--temperatura", type=float, default=0.6)
    ap.add_argument("--firma", default="Mireia Borras · Desarrollo de Negocio · Empresa")
    ap.add_argument("--sin_ejemplos", action="store_true",
                    help="ablacion: genera sin los ejemplos resueltos, para "
                         "medir cuanto aportan")
    ap.add_argument("--solo_confianza_alta", action="store_true",
                    help="genera solo donde el emparejamiento es claro")
    ap.add_argument("--salida", default="a5_correos.csv")
    a = ap.parse_args()

    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print("=" * 70)
    print("A5 · GENERACION DE CORREOS")
    print(f"     {VERSION_SCRIPT}")
    print(f"     ejemplos resueltos: {'NO (ablacion)' if a.sin_ejemplos else 'SI'}")
    print("=" * 70)
    if not torch.cuda.is_available():
        print("\n*** SIN GPU: ejecutalo en Colab ***")
        sys.exit(1)
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    catalogo = leer_catalogo()
    d = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                   for p in ["train", "val", "test"]], ignore_index=True)
    d = d[d.tiene_texto.fillna(False)].sample(n=300, random_state=42).reset_index(drop=True)

    # emparejar
    print("\nEmparejando...")
    emb = SentenceTransformer("intfloat/multilingual-e5-small")
    V = emb.encode(["passage: " + texto_servicio(s) for s in catalogo],
                   normalize_embeddings=True)
    W = emb.encode(["query: " + t[:MAX_CARACTERES] for t in d.web_text.fillna("")],
                   normalize_embeddings=True, batch_size=32)
    S = W @ V.T
    Z = (S - S.mean(axis=1, keepdims=True)) / S.std(axis=1, keepdims=True)
    orden = np.argsort(-Z, axis=1)
    i = np.arange(len(d))
    d["serv_idx"] = orden[:, 0]
    d["margen_z"] = Z[i, orden[:, 0]] - Z[i, orden[:, 1]]
    d["confianza"] = np.where(d.margen_z >= 0.8, "ALTA",
                     np.where(d.margen_z >= 0.3, "MEDIA", "BAJA"))
    print("   " + " · ".join(f"{k}: {v}" for k, v in d.confianza.value_counts().items()))

    sel = d[d.confianza == "ALTA"] if a.solo_confianza_alta else d
    sel = sel.head(a.muestra)
    print(f"\nGenerando {len(sel)} correos con {a.modelo}...")

    tok = AutoTokenizer.from_pretrained(a.modelo)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    # Control de longitud del prompt ANTES de gastar GPU. Es el error X4: un
    # prompt que excede el limite se trunca en silencio y lo que se pierde es
    # el final, es decir, la empresa que hay que atender.
    prueba = tok.apply_chat_template(
        construir_mensajes("EMPRESA DE PRUEBA", "x" * MAX_CARACTERES,
                           catalogo[0], a.firma, not a.sin_ejemplos),
        tokenize=False, add_generation_prompt=True)
    n_prompt = len(tok(prueba).input_ids)
    MAX_ENTRADA = 4096
    print(f"   prompt: {n_prompt} tokens (limite {MAX_ENTRADA})")
    if n_prompt > MAX_ENTRADA:
        sys.exit(f"El prompt excede el limite y se truncaria. Baja "
                 f"MAX_CARACTERES o quita un ejemplo.")

    from transformers import BitsAndBytesConfig
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
            construir_mensajes(r.empresa_clave, r.web_text,
                               catalogo[r.serv_idx], a.firma,
                               not a.sin_ejemplos),
            tokenize=False, add_generation_prompt=True) for r in lote.itertuples()]
        ent = tok(textos, return_tensors="pt", padding=True,
                  truncation=True, max_length=MAX_ENTRADA).to(modelo.device)
        with torch.no_grad():
            out = modelo.generate(**ent, max_new_tokens=400, do_sample=True,
                                  temperature=a.temperatura, top_p=0.9,
                                  repetition_penalty=1.05,
                                  pad_token_id=tok.pad_token_id)
        for r, o in zip(lote.itertuples(), out):
            correo = tok.decode(o[ent.input_ids.shape[1]:],
                                skip_special_tokens=True).strip()
            serv = catalogo[r.serv_idx]
            v = verificar(correo, r.web_text, serv, catalogo)
            filas.append({"empresa_clave": r.empresa_clave, "sector": r.sector,
                          "servicio": serv["codigo"], "confianza": r.confianza,
                          "correo": correo, **v})
        print(f"   {len(filas)}/{len(sel)}")

    e = pd.DataFrame(filas)

    print("\n" + "=" * 70)
    print("EVALUACION")
    print("=" * 70)
    print(f"   correos generados          : {len(e)}")
    print(f"   longitud media             : {e.palabras.mean():.0f} palabras "
          f"(rango {e.palabras.min()}-{e.palabras.max()})")
    print(f"   dentro de 110-200 palabras : {e.cumple_longitud.mean()*100:.1f}%")

    print(f"\n   ESTRUCTURA DE CORREO  <- lo que fallaba en la v1")
    print(f"      tiene saludo            : {e.tiene_saludo.mean()*100:5.1f}%")
    print(f"      tiene despedida         : {e.tiene_despedida.mean()*100:5.1f}%")
    print(f"      agradece la atencion    : {e.agradece.mean()*100:5.1f}%")
    print(f"      termina con pregunta    : {e.tiene_pregunta.mean()*100:5.1f}%")
    completos = (e.tiene_saludo & e.tiene_despedida & e.agradece
                 & e.tiene_pregunta)
    print(f"      LOS CUATRO A LA VEZ     : {completos.mean()*100:5.1f}%")

    print(f"\n   TICS DE LA v1  <- deberian ser 0")
    print(f"      marcador sin rellenar   : {e.marcador_sin_rellenar.mean()*100:5.1f}%"
          f"   (v1: 7,5%)")
    print(f"      se delata leyendo web   : {e.se_delata_leyendo_web.mean()*100:5.1f}%"
          f"   (v1: 15,0%)")

    print(f"\n   FUNDAMENTACION")
    print(f"      media                   : {e.fundamentacion.mean()*100:5.1f}%")
    print(f"      OJO: bajara respecto a la v1 solo por anadir cortesia.")
    print(f"      Compara la DISTANCIA AL SUELO, no el porcentaje:")
    print(f"      python scripts/F5_A5_E19_control_fundamentacion.py")

    print(f"\n   menciona servicios ajenos  : {e.menciona_servicio_ajeno.mean()*100:.1f}%"
          f"  <- riesgo real, debe ser 0")

    if e.confianza.nunique() > 1:
        print("\n   Segun la confianza del emparejamiento:")
        for c in ["ALTA", "MEDIA", "BAJA"]:
            s = e[e.confianza == c]
            if len(s):
                print(f"      {c:<6} n={len(s):>3}  fundamentacion "
                      f"{s.fundamentacion.mean()*100:5.1f}%")

    e.to_csv(SALIDA / a.salida, index=False, encoding="utf-8")
    print(f"\n   Guardado: {a.salida}  (revisa una muestra a mano)")


if __name__ == "__main__":
    main()
