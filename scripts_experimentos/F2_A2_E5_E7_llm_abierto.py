"""
CLASIFICACION CON UN LLM ABIERTO  ·  paso 5 del agente A2
==========================================================
Mide si un modelo de lenguaje generalista entiende la taxonomia de Empresa
sin que nadie se la ensene.

LA PREGUNTA
-----------
El modelo supervisado (entrenado con vuestro historico) acierta el 48,9% a
nivel de sector. La pregunta del TFM es: un LLM que nunca ha visto vuestros
datos, solo con la lista de sectores delante, ¿cuanto acierta?

Con ChatGPT y el dataset antiguo la respuesta era 40,5%. Aqui se repite el
experimento con un modelo ABIERTO, que es lo que se puede usar en el master.

DOS MODOS
---------
  zero-shot : se le da solo la lista de 41 sectores.
              ¿Entiende la taxonomia por su cuenta?

  few-shot  : se le da la lista MAS 20 ejemplos ya resueltos.
              ¿Aprende la convencion de la casa viendo ejemplos?

La diferencia entre ambos es el resultado interesante. Si few-shot mejora
mucho, la convencion se puede transmitir. Si apenas mejora, hace falta
entrenamiento real sobre miles de casos, que es la tesis del trabajo.

DONDE SE EJECUTA
----------------
En Google Colab con GPU. En un portatil sin tarjeta grafica tardaria dias.

    !pip install -q transformers accelerate bitsandbytes
    !python F2_A2_E5_E7_llm_abierto.py --modo zero --muestra 600
    !python F2_A2_E5_E7_llm_abierto.py --modo few  --muestra 600

PRIVACIDAD: solo imprime metricas agregadas.
"""

import argparse
import json
import re
import sys
import unicodedata
import warnings
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
MAX_CARACTERES_WEB = 1200      # texto de la empresa que se va a clasificar
MAX_CARACTERES_EJEMPLO = 350   # texto de cada ejemplo resuelto del few-shot
MAX_TOKENS_PROMPT = 8192       # Qwen2.5 admite mucho mas; 8k va sobrado
NIVEL = "sector"

# Por que dos limites distintos:
#   Con 20 ejemplos a 1.200 caracteres el prompt se iba a ~6.700 tokens y se
#   cortaba, dejando fuera la empresa que habia que clasificar. Los ejemplos
#   solo tienen que mostrar el ESTILO de la decision, no requieren la web
#   entera, asi que se recortan a 350 caracteres.


# ==========================================================================
# Prompt
# ==========================================================================

INSTRUCCION = """Eres un analista del instituto tecnologico Empresa. Clasificas \
empresas dentro de la taxonomia sectorial INTERNA de Empresa.

Importante: esta taxonomia es propia de Empresa y no siempre coincide con la \
clasificacion habitual de un sector. Usa EXCLUSIVAMENTE una de las categorias \
de la lista, copiada literalmente.

CATEGORIAS DISPONIBLES:
{categorias}

Responde UNICAMENTE con el nombre exacto de una categoria. Sin explicaciones."""


def ficha_empresa(fila, es_ejemplo=False):
    limite = MAX_CARACTERES_EJEMPLO if es_ejemplo else MAX_CARACTERES_WEB
    partes = [f"Nombre: {fila.empresa}"]
    if isinstance(fila.pais, str) and fila.pais.strip():
        partes.append(f"Pais: {fila.pais}")
    texto = str(fila.web_text or "")[:limite]
    if texto.strip():
        partes.append(f"Texto de su web: {texto}")
    else:
        partes.append("Texto de su web: (no disponible)")
    return "\n".join(partes)


def construir_mensajes(fila, categorias, ejemplos=None):
    msgs = [{"role": "system",
             "content": INSTRUCCION.format(categorias="\n".join(f"- {c}" for c in categorias))}]
    for e in (ejemplos or []):
        msgs.append({"role": "user", "content": ficha_empresa(e, es_ejemplo=True)})
        msgs.append({"role": "assistant", "content": getattr(e, NIVEL)})
    msgs.append({"role": "user", "content": ficha_empresa(fila)})
    return msgs


# ==========================================================================
# Normalizacion de la respuesta
# ==========================================================================

def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).upper())
                   if unicodedata.category(c) != "Mn")


def mapear_a_categoria(respuesta, categorias):
    """El modelo puede responder con variaciones. Se lleva a la categoria
    valida mas parecida. Si no se parece a ninguna, se marca como invalida."""
    if not respuesta:
        return None, "vacia"
    r = sin_acentos(re.sub(r"[\"'`*\-\n]", " ", respuesta)).strip()
    r = re.sub(r"\s+", " ", r)

    normalizadas = {sin_acentos(c): c for c in categorias}
    if r in normalizadas:
        return normalizadas[r], "exacta"
    for n, c in normalizadas.items():          # contenida
        if n in r or r in n:
            return c, "contenida"
    mejor, punt = None, 0.0                    # parecido
    for n, c in normalizadas.items():
        p = SequenceMatcher(None, r, n).ratio()
        if p > punt:
            mejor, punt = c, p
    if punt >= 0.75:
        return mejor, "aproximada"
    return None, "invalida"


# ==========================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="Qwen/Qwen2.5-7B-Instruct",
                    help="Qwen/Qwen2.5-7B-Instruct | meta-llama/Llama-3.1-8B-Instruct "
                         "| BSC-LT/salamandra-7b-instruct")
    ap.add_argument("--modo", choices=["zero", "few"], default="zero")
    ap.add_argument("--muestra", type=int, default=600)
    ap.add_argument("--ejemplos", type=int, default=20, help="solo para --modo few")
    ap.add_argument("--lote", type=int, default=8)
    ap.add_argument("--sin-cuantizar", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    etiqueta = f"{a.modelo.split('/')[-1]}_{a.modo}"
    print("=" * 74)
    print(f"LLM ABIERTO · {etiqueta}")
    print("=" * 74)

    if not torch.cuda.is_available():
        print("\n*** SIN GPU ***")
        print("Esto en CPU tarda dias. Ejecutalo en Colab con GPU:")
        print("   Entorno de ejecucion > Cambiar tipo de entorno > GPU")
        sys.exit(1)
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    # ---- datos ---------------------------------------------------------
    tr = pd.read_csv(DATOS / "cuentas_train.csv")
    te = pd.read_csv(DATOS / "cuentas_test.csv")
    for d in (tr, te):
        d["web_text"] = d.web_text.fillna("")
        d["pais"] = d.pais.fillna("")

    categorias = sorted(tr[NIVEL].dropna().unique())
    te = te[te[NIVEL].isin(categorias)]
    muestra = te.sample(n=min(a.muestra, len(te)), random_state=SEMILLA)
    print(f"Categorias: {len(categorias)}   ·   Muestra: {len(muestra)}")
    print(f"Con texto web: {muestra.tiene_texto.mean()*100:.1f}%")

    ejemplos = None
    if a.modo == "few":
        # un ejemplo por sector, empezando por los mas frecuentes,
        # y siempre del conjunto de ENTRENAMIENTO (nunca del test)
        con_texto = tr[tr.tiene_texto.fillna(False)]
        ejemplos = (con_texto.groupby(NIVEL, group_keys=False)
                             .head(1)
                             .head(a.ejemplos))
        ejemplos = list(ejemplos.itertuples())
        print(f"Ejemplos en el prompt: {len(ejemplos)}")

    # ---- modelo ---------------------------------------------------------
    print(f"\nCargando {a.modelo}...")
    tok = AutoTokenizer.from_pretrained(a.modelo)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    kwargs = {"torch_dtype": torch.float16, "device_map": "auto"}
    if not a.sin_cuantizar:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True)
        print("   (cuantizado a 4 bits: ocupa 4 veces menos y pierde muy poco)")
    modelo = AutoModelForCausalLM.from_pretrained(a.modelo, **kwargs)
    modelo.eval()

    # ---- inferencia por lotes -------------------------------------------
    print(f"\nClasificando en lotes de {a.lote}...\n")
    filas = list(muestra.itertuples())
    resultados = []
    import time
    t0 = time.time()

    for i in range(0, len(filas), a.lote):
        lote = filas[i:i + a.lote]
        textos = [tok.apply_chat_template(
                     construir_mensajes(f, categorias, ejemplos),
                     tokenize=False, add_generation_prompt=True) for f in lote]
        ent = tok(textos, return_tensors="pt", padding=True,
                  truncation=True, max_length=MAX_TOKENS_PROMPT).to(modelo.device)
        with torch.no_grad():
            sal = modelo.generate(**ent, max_new_tokens=24, do_sample=False,
                                  pad_token_id=tok.pad_token_id)
        for f, s in zip(lote, sal):
            bruta = tok.decode(s[ent.input_ids.shape[1]:],
                               skip_special_tokens=True).strip()
            pred, como = mapear_a_categoria(bruta, categorias)
            resultados.append({
                "empresa_clave": f.empresa_clave,
                "respuesta_cruda": bruta[:200],
                "real": getattr(f, NIVEL),
                "prediccion": pred,
                "mapeo": como,
                "tiene_texto": bool(f.tiene_texto),
                "acierto": pred == getattr(f, NIVEL),
            })
        hechas = len(resultados)
        if hechas % (a.lote * 5) == 0 or hechas == len(filas):
            ok = sum(r["acierto"] for r in resultados)
            trans = time.time() - t0
            print(f"   {hechas:>4}/{len(filas)}   acierto {ok/hechas*100:5.2f}%   "
                  f"quedan ~{(len(filas)-hechas)*trans/hechas/60:.0f} min")

    # ---- resultados ------------------------------------------------------
    r = pd.DataFrame(resultados)
    acc = r.acierto.mean() * 100
    from sklearn.metrics import f1_score
    f1 = f1_score(r.real, r.prediccion.fillna("(invalida)"),
                  average="macro", zero_division=0) * 100

    print("\n" + "=" * 74)
    print("RESULTADO")
    print("=" * 74)
    print(f"   aciertos   : {acc:.2f}%")
    print(f"   f1_macro   : {f1:.2f}")
    print(f"   tiempo     : {(time.time()-t0)/60:.1f} min")

    print("\n   Segun disponibilidad de texto web:")
    for tiene, g in r.groupby("tiene_texto"):
        print(f"      {'CON texto' if tiene else 'SIN texto':<11} n={len(g):>4}   "
              f"acierto {g.acierto.mean()*100:5.2f}%")

    print("\n   Como se interpreto la respuesta del modelo:")
    for k, n in r.mapeo.value_counts().items():
        print(f"      {k:<12} {n:>4}  ({n/len(r)*100:4.1f}%)")

    print("\n   COMPARATIVA (nivel sector, 41 clases)")
    print(f"      clase mayoritaria ................. 13,16%")
    print(f"      modelo supervisado (TF-IDF+SVM) ... 48,91%")
    print(f"      {etiqueta:<33} {acc:5.2f}%")

    r.to_csv(SALIDA / f"llm_{etiqueta}.csv", index=False, encoding="utf-8")
    with open(SALIDA / f"llm_{etiqueta}.json", "w", encoding="utf-8") as fh:
        json.dump({"modelo": a.modelo, "modo": a.modo, "n": len(r),
                   "accuracy": round(acc, 2), "f1_macro": round(f1, 2)},
                  fh, ensure_ascii=False, indent=2)
    print(f"\n   Guardado: llm_{etiqueta}.csv")


if __name__ == "__main__":
    main()
