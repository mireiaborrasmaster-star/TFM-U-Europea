# -*- coding: utf-8 -*-
"""
PREP_recuperar_seccion_perdida.py - rescata texto escrito y luego perdido
=========================================================================

POR QUE EXISTE
    El 03-10-2026 se descubrio que el apartado 4.6.5 del capitulo de
    resultados -el del orquestador, que es el que cierra el objetivo 3-
    habia desaparecido de memoria/CAP4_6_resultados.md. No hay copia de
    seguridad del fichero. Queda registrado como error X22.

    El texto si existe en la transcripcion de la sesion que lo escribio:
    cada llamada a las herramientas de escritura queda grabada ahi con su
    contenido completo. Este script la lee y extrae el texto.

QUE HACE
    Recorre el .jsonl de la transcripcion, localiza las llamadas a Write y
    Edit cuyo contenido incluye el texto buscado, y deja cada candidato en
    un fichero aparte para poder compararlos y elegir el mas completo.

    NO ESCRIBE EN LA MEMORIA. Solo deja los candidatos en un directorio de
    trabajo; el montaje final se hace a mano y se revisa.

COMO SE EJECUTA
    python scripts/PREP_recuperar_seccion_perdida.py "El sistema secuencial"
"""

import json
import sys
from pathlib import Path

VERSION_SCRIPT = "v1 - 03-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
TRANSCRIPCIONES = Path.home() / ".claude" / "projects"
SALIDA = RAIZ / "datos" / "04_recuperado"

CAMPOS_TEXTO = ("content", "new_string", "old_string")


def candidatos(jsonl, buscado):
    """Devuelve (indice_linea, herramienta, fichero, campo, texto)."""
    out = []
    with open(jsonl, encoding="utf-8") as f:
        for i, linea in enumerate(f, 1):
            if buscado not in linea:
                continue
            try:
                reg = json.loads(linea)
            except json.JSONDecodeError:
                continue
            msg = reg.get("message") or {}
            cont = msg.get("content")
            if not isinstance(cont, list):
                continue
            for bloque in cont:
                if not isinstance(bloque, dict):
                    continue
                if bloque.get("type") != "tool_use":
                    continue
                nombre = bloque.get("name", "")
                entrada = bloque.get("input") or {}
                destino = entrada.get("file_path", "")
                for campo in CAMPOS_TEXTO:
                    txt = entrada.get(campo)
                    if isinstance(txt, str) and buscado in txt:
                        out.append((i, nombre, destino, campo, txt))
    return out


def main():
    buscado = sys.argv[1] if len(sys.argv) > 1 else "El sistema secuencial"

    print()
    print("=" * 74)
    print(f"PREP - recuperar seccion perdida  ·  {VERSION_SCRIPT}")
    print("=" * 74)
    print()
    print(f"   Buscando: {buscado!r}")
    print()

    jsonls = sorted(TRANSCRIPCIONES.rglob("*.jsonl"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    if not jsonls:
        raise SystemExit("   No encuentro transcripciones en ~/.claude/projects")

    SALIDA.mkdir(parents=True, exist_ok=True)
    total = 0
    for jsonl in jsonls:
        encontrados = candidatos(jsonl, buscado)
        if not encontrados:
            continue
        print(f"   {jsonl.name[:8]}...  {len(encontrados)} candidato(s)")
        for i, nombre, destino, campo, txt in encontrados:
            total += 1
            etiqueta = Path(destino).name or "sin_fichero"
            f = SALIDA / f"cand_{total:02d}_{jsonl.name[:8]}_L{i}_{nombre}_{campo}.md"
            f.write_text(txt, encoding="utf-8")
            print(f"      L{i:<7} {nombre:<6} {campo:<11} "
                  f"{len(txt):>7} car  {etiqueta}")

    print()
    if total == 0:
        print("   Nada encontrado. Prueba con otro fragmento de texto.")
    else:
        print(f"   [ok] {total} candidato(s) en {SALIDA.relative_to(RAIZ)}")
        print("   Compara los mas largos: el bueno suele ser el Write completo")
        print("   o el new_string de la Edit que lo inserto.")
    print()


if __name__ == "__main__":
    main()
