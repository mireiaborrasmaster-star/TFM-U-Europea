"""
PASO 6 · ENTRENAR EL TRANSFORMER
=================================
Ajusta un transformer multilingue a la taxonomia de Empresa.

QUE SE ESTA PROBANDO
--------------------
Ya sabemos dos cosas:
  · Un LLM que ENTIENDE lenguaje pero NO conoce la convencion .... 33,3%
  · Un modelo que CONOCE la convencion pero NO entiende lenguaje . 48,9%

Falta la tercera esquina: un modelo que haga las dos cosas. Eso es este.

Si gana, la conclusion es que hacen falta los dos ingredientes.
Si empata con el modelo lineal, la conclusion es que la tarea se resuelve
por vocabulario y la comprension semantica no aporta. Tambien es un
resultado valido, y responde a una pregunta que el tribunal va a hacer.

POR QUE DEBERIA GANAR
---------------------
  · SINONIMOS. Para el modelo lineal "envase" y "embalaje" son simbolos sin
    relacion. El transformer sabe que significan lo mismo.
  · IDIOMAS. El 25% de las cuentas son internacionales. El modelo lineal
    tiene que aprender "packaging", "Verpackung" e "imballaggio" por separado.
    El transformer multilingue ya sabe que son lo mismo.
  · COLA LARGA. En sectores con 30 ejemplos el modelo lineal no tiene
    material; el transformer llega con el vocabulario ya aprendido.
  -> La mejora deberia verse sobre todo en el F1-MACRO.

DISENO
------
Una sola cabeza jerarquica con dos salidas: sector (41) y subsector (169).
El nivel agrupado (12) NO se predice aparte: se deriva del sector, porque la
jerarquia es limpia (ningun sector cuelga de dos agrupados). Es el principio
de "entrenar fino y agregar despues".

Se anade un termino de coherencia que penaliza predecir un subsector que no
pertenece al sector predicho.

Uso en Colab:
    !pip install -q transformers accelerate
    !python scripts/F2_A2_E8_E10_transformer.py --epocas 4
"""

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import Dataset
from transformers import (AutoConfig, AutoModel, AutoTokenizer, Trainer,
                          TrainingArguments, set_seed)

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
IGNORAR = -100
VERSION_SCRIPT = "v2 · 27-09-2026 · metricas corregidas"



# ---------------------------------------------------------------------------
# LA BIBLIOTECA DE SECTORES  (experimento E31)
# ---------------------------------------------------------------------------
# Las descripciones de cada sector, escritas por la organizacion, con criterio
# de inclusion y de exclusion. La pregunta es si el modelo aprende mejor
# empezando por saber QUE significa cada clase, en vez de deducirlo solo de
# los ejemplos.
#
# Donde se inyectan: en `cab_sec`, que es una sola capa lineal que recibe
# directamente la media enmascarada del encoder. Las descripciones se
# codifican POR ESA MISMA VIA, asi que viven en el mismo espacio.
# (Haberlo hecho sobre otra arquitectura fue el error X20.)

def cargar_biblioteca(ruta=None):
    """Devuelve {SECTOR_SIN_ACENTOS: descripcion} o None si no hay fichero."""
    import json
    import unicodedata
    candidatos = [ruta] if ruta else [
        RAIZ / "datos" / "taxonomia_completa (1).json",
        RAIZ / "datos" / "taxonomia_completa.json",
        Path("taxonomia_completa (1).json"),
        Path("taxonomia_completa.json"),
    ]
    for c in candidatos:
        if c and Path(c).exists():
            tax = json.loads(Path(c).read_text(encoding="utf-8"))
            def quita(t):
                return "".join(x for x in unicodedata.normalize("NFD", str(t).upper().strip())
                               if unicodedata.category(x) != "Mn")
            return ({quita(k): v.get("descripcion", k)
                     for k, v in tax.items() if isinstance(v, dict)}, Path(c).name)
    return None, None


def inicializar_con_biblioteca(modelo, tok, sectores, bib, disp, congelar):
    """
    Pone en `cab_sec` la descripcion de cada sector, ya codificada.

    La escala importa: se normalizan los vectores y se reescalan a la misma
    desviacion tipica que tendria la inicializacion por defecto. Asi se
    conserva la geometria —que descripcion esta cerca de cual— sin
    desajustar la optimizacion.
    """
    import unicodedata

    def quita(t):
        return "".join(x for x in unicodedata.normalize("NFD", str(t).upper().strip())
                       if unicodedata.category(x) != "Mn")

    textos, sin_desc = [], []
    for c in sectores:
        d = bib.get(quita(c))
        if d:
            textos.append(d)
        else:
            textos.append(f"Empresas del sector {str(c).lower()}.")
            sin_desc.append(c)

    modelo.eval()
    vs = []
    with torch.no_grad():
        for i in range(0, len(textos), 16):
            e = tok(textos[i:i + 16], truncation=True, max_length=256,
                    padding=True, return_tensors="pt")
            e = {k: v.to(disp) for k, v in e.items()}
            vs.append(modelo._pool(e["input_ids"], e["attention_mask"]).cpu())
    V = torch.cat(vs)
    V = V / V.norm(dim=1, keepdim=True).clamp(min=1e-9)
    # .item() porque V esta en CPU y el parametro en la GPU: sin esto,
    # multiplicar un tensor de CPU por un escalar de CUDA falla.
    # La escala importa y es facil equivocarse. Normalizar las filas deja los
    # valores en ~1/raiz(768), asi que multiplicar por la desviacion tipica da
    # una matriz 28 veces mas pequena de lo que se pretende. Hay que REESCALAR:
    #    nueva_desviacion = la que tendria la inicializacion por defecto
    # .item() ademas evita el choque CPU/GPU que fue el fallo X21.
    objetivo = modelo.cab_sec.weight.detach().std().item()
    V = V * (objetivo / V.std().clamp(min=1e-9).item())

    with torch.no_grad():
        modelo.cab_sec.weight.copy_(V.to(modelo.cab_sec.weight.device))
        modelo.cab_sec.bias.zero_()
    if congelar:
        for q in modelo.cab_sec.parameters():
            q.requires_grad = False
    modelo.train()
    return sin_desc


class DatosCuentas(Dataset):
    def __init__(self, textos, y_sec, y_sub, tok, max_len):
        self.enc = tok(list(textos), truncation=True, max_length=max_len,
                       padding="max_length", return_tensors="pt")
        self.y_sec = torch.tensor(y_sec, dtype=torch.long)
        self.y_sub = torch.tensor(y_sub, dtype=torch.long)

    def __len__(self):
        return len(self.y_sec)

    def __getitem__(self, i):
        d = {k: v[i] for k, v in self.enc.items()}
        d["labels"] = self.y_sec[i]
        d["labels_sub"] = self.y_sub[i]
        return d


class ClasificadorJerarquico(nn.Module):
    """Encoder compartido + dos cabezas.

    Perdida = L_sector + alfa*L_subsector + beta*L_coherencia
    """

    def __init__(self, nombre, n_sec, n_sub, sub_a_sec, pesos=None,
                 alfa=0.3, beta=0.1, dropout=0.2):
        super().__init__()
        self.config = AutoConfig.from_pretrained(nombre)
        self.encoder = AutoModel.from_pretrained(nombre)
        h = self.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.cab_sec = nn.Linear(h, n_sec)
        self.cab_sub = nn.Linear(h, n_sub)
        self.alfa, self.beta = alfa, beta
        self.perdida_sec = nn.CrossEntropyLoss(weight=pesos)
        self.perdida_sub = nn.CrossEntropyLoss(ignore_index=IGNORAR)
        self.register_buffer("sub_a_sec", torch.tensor(sub_a_sec, dtype=torch.long))

    def _pool(self, ids, mask):
        """Media enmascarada. Con textos web largos y ruidosos es mas estable
        que usar el token CLS."""
        h = self.encoder(input_ids=ids, attention_mask=mask).last_hidden_state
        m = mask.unsqueeze(-1).float()
        return (h * m).sum(1) / m.sum(1).clamp(min=1e-9)

    def forward(self, input_ids=None, attention_mask=None, labels=None,
                labels_sub=None, **kw):
        x = self.dropout(self._pool(input_ids, attention_mask))
        lg_sec, lg_sub = self.cab_sec(x), self.cab_sub(x)
        perdida = None
        if labels is not None:
            perdida = self.perdida_sec(lg_sec, labels)
            if labels_sub is not None and self.alfa > 0:
                perdida = perdida + self.alfa * self.perdida_sub(lg_sub, labels_sub)
            if self.beta > 0:
                p_sub = torch.softmax(lg_sub, dim=-1)
                coincide = (self.sub_a_sec.unsqueeze(0) == labels.unsqueeze(1)).float()
                masa = (p_sub * coincide).sum(1).clamp(min=1e-9)
                perdida = perdida + self.beta * (-torch.log(masa)).mean()
        return {"loss": perdida, "logits": lg_sec, "logits_sub": lg_sub}



def argumentos_compatibles(clase, **kw):
    """Filtra los argumentos segun lo que acepte la version instalada.

    `transformers` cambia el nombre de algunos parametros entre versiones
    (warmup_ratio, eval_strategy / evaluation_strategy...). En lugar de fijar
    una version concreta, se le pasa solo lo que su firma admite y se avisa
    de lo que se descarta.
    """
    import inspect
    validos = set()
    try:
        validos |= set(inspect.signature(clase.__init__).parameters)
    except (TypeError, ValueError):
        pass
    if hasattr(clase, "__dataclass_fields__"):
        validos |= set(clase.__dataclass_fields__)

    # equivalencias conocidas entre versiones
    alias = {"eval_strategy": "evaluation_strategy",
             "evaluation_strategy": "eval_strategy"}
    final, descartados = {}, []
    for k, v in kw.items():
        if k in validos:
            final[k] = v
        elif alias.get(k) in validos:
            final[alias[k]] = v
        else:
            descartados.append(k)
    if descartados:
        print(f"   (esta version de transformers no admite: {', '.join(descartados)};"
              f" se continua sin ellos)")
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="xlm-roberta-base")
    ap.add_argument("--campo", default="input_completo",
                    choices=["input_completo", "input_nombre", "input_texto"])
    ap.add_argument("--max_len", type=int, default=256)
    ap.add_argument("--epocas", type=int, default=4)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--alfa", type=float, default=0.3)
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--sin_pesos", action="store_true")
    ap.add_argument("--biblioteca", default="no",
                    choices=["no", "inicial", "fija"],
                    help="no: como siempre · inicial: la cabeza arranca con "
                         "las descripciones y luego se mueve · fija: la cabeza "
                         "se queda clavada en ellas (experimento E31)")
    ap.add_argument("--taxonomia", default=None,
                    help="ruta al json con las descripciones; si no, se busca")
    ap.add_argument("--etiqueta", default=None)
    a = ap.parse_args()

    etiqueta = a.etiqueta or f"{a.modelo.split('/')[-1]}_{a.campo}"
    set_seed(SEMILLA)
    disp = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 70)
    print(f"PASO 6 · TRANSFORMER · {etiqueta}")
    print(f"script {VERSION_SCRIPT}")
    print("=" * 70)
    if disp == "cpu":
        print("\n*** SIN GPU: esto tardaria dias. Usa Colab con GPU. ***")
        return
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    tr = pd.read_csv(DATOS / "cuentas_train.csv")
    va = pd.read_csv(DATOS / "cuentas_val.csv")
    te = pd.read_csv(DATOS / "cuentas_test.csv")
    for d in (tr, va, te):
        d[a.campo] = d[a.campo].fillna("").astype(str)

    sectores = sorted(tr.sector.dropna().unique())
    sec_id = {s: i for i, s in enumerate(sectores)}
    subs = sorted(tr.subsector_agr.dropna().unique())
    sub_id = {s: i for i, s in enumerate(subs)}
    print(f"\nSectores: {len(sectores)} · Subsectores: {len(subs)}")
    print(f"train {len(tr):,} · val {len(va):,} · test {len(te):,}".replace(",", "."))

    # subsector -> sector padre mayoritario
    padre = (tr.dropna(subset=["subsector_agr"]).groupby("subsector_agr").sector
               .agg(lambda s: s.value_counts().idxmax()))
    sub_a_sec = [sec_id.get(padre.get(s), 0) for s in subs]

    # sector -> agrupado, para derivar el tercer nivel sin predecirlo
    sec_a_agr = (tr.dropna(subset=["sector_agrupado"]).groupby("sector").sector_agrupado
                   .agg(lambda s: s.value_counts().idxmax()).to_dict())

    def codif(d):
        ys = d.sector.map(sec_id).fillna(IGNORAR).astype(int).values
        yb = d.subsector_agr.map(sub_id)
        return ys, yb.where(yb.notna(), IGNORAR).astype(int).values

    y_tr, ys_tr = codif(tr)
    y_va, ys_va = codif(va)
    y_te, ys_te = codif(te)
    ok = y_va >= 0
    va, y_va, ys_va = va[ok], y_va[ok], ys_va[ok]
    ok = y_te >= 0
    te, y_te, ys_te = te[ok], y_te[ok], ys_te[ok]

    pesos = None
    if not a.sin_pesos:
        c = np.bincount(y_tr, minlength=len(sectores)).astype(float)
        # raiz del inverso: el inverso puro desestabiliza con ratios altos
        w = np.sqrt(c.sum() / (len(sectores) * np.maximum(c, 1)))
        pesos = torch.tensor(w, dtype=torch.float, device=disp)
        print(f"Pesos por clase: min {w.min():.2f} · max {w.max():.2f}")

    tok = AutoTokenizer.from_pretrained(a.modelo)
    ds_tr = DatosCuentas(tr[a.campo], y_tr, ys_tr, tok, a.max_len)
    ds_va = DatosCuentas(va[a.campo], y_va, ys_va, tok, a.max_len)
    ds_te = DatosCuentas(te[a.campo], y_te, ys_te, tok, a.max_len)

    modelo = ClasificadorJerarquico(a.modelo, len(sectores), len(subs), sub_a_sec,
                                    pesos, a.alfa, a.beta).to(disp)

    # --- la biblioteca de sectores, si se pide (E31) ----------------------
    sin_descripcion = []
    if a.biblioteca != "no":
        bib, fichero = cargar_biblioteca(a.taxonomia)
        if bib is None:
            sys.exit("No encuentro la taxonomia con descripciones. "
                     "Ponla en datos/ o pasa --taxonomia RUTA")
        print(f"\nBIBLIOTECA · {fichero}")
        print(f"   modo: {a.biblioteca}  "
              f"({'arranca con las descripciones y se mueve' if a.biblioteca == 'inicial' else 'clavada en las descripciones'})")
        sin_descripcion = inicializar_con_biblioteca(
            modelo, tok, sectores, bib, disp, congelar=(a.biblioteca == "fija"))
        print(f"   sectores con descripcion propia: "
              f"{len(sectores) - len(sin_descripcion)} de {len(sectores)}")
        if sin_descripcion:
            print(f"   sin descripcion (se usa el nombre): "
                  f"{', '.join(map(str, sin_descripcion))}")

    def primero(x):
        """Al declarar dos etiquetas (labels y labels_sub), el Trainer devuelve
        las dos juntas. Aqui solo interesa la primera: el sector."""
        if isinstance(x, (tuple, list)):
            return np.asarray(x[0])
        x = np.asarray(x)
        if x.ndim == 2 and x.shape[0] == 2 and x.shape[1] != 2:
            return x[0]
        return x

    def met(p):
        lg = primero(p.predictions)
        yt = primero(p.label_ids)
        yp = np.argmax(lg, -1)
        m = yt >= 0                      # ignora las filas sin etiqueta
        yt, yp = yt[m], yp[m]
        return {"accuracy": accuracy_score(yt, yp),
                "f1_macro": f1_score(yt, yp, average="macro", zero_division=0)}

    cfg = TrainingArguments(**argumentos_compatibles(
        TrainingArguments,
        output_dir=str(SALIDA / f"ckpt_{etiqueta}"),
        num_train_epochs=a.epocas,
        per_device_train_batch_size=a.batch,
        per_device_eval_batch_size=a.batch * 2,
        learning_rate=a.lr,
        warmup_ratio=0.1,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        save_total_limit=1,
        logging_steps=100,
        fp16=True,
        report_to="none",
        seed=SEMILLA,
        label_names=["labels", "labels_sub"],
    ))
    ent = Trainer(**argumentos_compatibles(
        Trainer, model=modelo, args=cfg, train_dataset=ds_tr,
        eval_dataset=ds_va, compute_metrics=met,
        processing_class=tok))

    print(f"\nEntrenando {a.epocas} epocas...\n")
    ent.train()

    # ---- evaluacion en los tres niveles ---------------------------------
    print("\n" + "=" * 70)
    print("RESULTADOS EN TEST")
    print("=" * 70)
    pred = ent.predict(ds_te)
    lg = primero(pred.predictions)
    yp = np.argmax(lg, -1)
    te = te.copy()
    te["pred_sector"] = [sectores[i] for i in yp]
    te["pred_agrupado"] = te.pred_sector.map(sec_a_agr)

    resultados = {}
    for nivel, real, prediccion in [
        ("Sector agrupado (12)", te.sector_agrupado, te.pred_agrupado),
        ("Sector (41)", te.sector, te.pred_sector),
    ]:
        m = real.notna() & prediccion.notna()
        acc = accuracy_score(real[m], prediccion[m]) * 100
        f1 = f1_score(real[m], prediccion[m], average="macro", zero_division=0) * 100
        resultados[nivel] = {"accuracy": round(acc, 2), "f1_macro": round(f1, 2),
                             "n": int(m.sum())}
        print(f"   {nivel:<22} n={int(m.sum()):>5}   acc {acc:6.2f}   f1_macro {f1:6.2f}")

    te["acierto"] = te.pred_sector == te.sector
    print("\n   Segun disponibilidad de texto web (nivel sector):")
    for tiene, g in te.groupby("tiene_texto"):
        print(f"      {'CON texto' if tiene else 'SIN texto':<11} n={len(g):>5}   "
              f"acc {g.acierto.mean()*100:6.2f}")

    if "jerarquia_incoherente" in te.columns:
        print("\n   Filas con jerarquia incoherente:")
        for v, g in te.groupby(te.jerarquia_incoherente.fillna(False)):
            print(f"      {'incoherente' if v else 'coherente':<11} n={len(g):>5}   "
                  f"acc {g.acierto.mean()*100:6.2f}")

    print("\n   COMPARATIVA · nivel sector, 41 clases")
    print("      responder siempre lo mas comun ..... 13,16   f1m  0,57")
    print("      LLM abierto zero-shot .............. 33,33   f1m 25,12")
    print("      LLM abierto few-shot ............... 34,67   f1m 24,37")
    print("      supervisado TF-IDF + SVM ........... 48,49   f1m 40,16")
    print("      supervisado regresion logistica .... 48,91   f1m 41,89")
    r = resultados["Sector (41)"]
    print(f"      {etiqueta:<34} {r['accuracy']:5.2f}   f1m {r['f1_macro']:5.2f}")

    te[["empresa_clave", "sector", "pred_sector", "sector_agrupado",
        "pred_agrupado", "acierto", "tiene_texto"]].to_csv(
        SALIDA / f"pred_{etiqueta}.csv", index=False, encoding="utf-8")
    with open(SALIDA / f"transformer_{etiqueta}.json", "w", encoding="utf-8") as f:
        json.dump({"biblioteca": a.biblioteca,
                   "sin_descripcion": [str(x) for x in sin_descripcion],
                   "modelo": a.modelo, "campo": a.campo, "epocas": a.epocas,
                   "max_len": a.max_len, "lr": a.lr,
                   "alfa": a.alfa, "beta": a.beta,
                   "pesos_por_clase": not a.sin_pesos,
                   "resultados": resultados}, f, ensure_ascii=False, indent=2)
    print(f"\n   Guardado: transformer_{etiqueta}.json")


if __name__ == "__main__":
    main()
