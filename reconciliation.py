"""
Módulo de conciliación robusto para TaxFlow-Diamond.

Reemplaza el enfoque anterior (merge_asof por "monto más cercano") que podía
generar falsos positivos: una partida se emparejaba con el monto más
parecido disponible en ESE MOMENTO del algoritmo, sin garantizar que fuera
realmente la mejor pareja posible, y sin evitar que un mismo registro se
usara en más de un cruce cuando había montos repetidos (nómina, facturas
con montos iguales, etc.).

Estrategia nueva, en dos pasadas:

  1) MATCH EXACTO: mismo monto (redondeado a 2 decimales) y misma fecha.
     Si hay duplicados exactos (dos pagos idénticos el mismo día), se
     emparejan uno a uno usando un contador de "ocurrencia" por grupo,
     nunca se cruzan todos-contra-todos.

  2) MATCH APROXIMADO (solo para lo que quedó sin conciliar): se buscan
     candidatos dentro de una tolerancia de monto y una ventana de días,
     se calcula un "puntaje" de cercanía (monto + fecha) para cada par
     candidato, y se asignan de forma GREEDY empezando por los mejores
     puntajes, marcando cada partida (banco y auxiliar) como usada tras
     su primer emparejamiento. Esto evita que una misma partida bancaria
     o contable se conte dos veces en la conciliación.

Esto es determinístico, auditable (se puede ver por qué se casó cada
partida) y evita el problema de "many-to-many" que producía el merge
simple en Nómina / IVA / Saldos.
"""

import numpy as np
import pandas as pd


def _preparar(df, col_monto, col_fecha, prefijo_id):
    df = df.dropna(subset=[col_monto, col_fecha]).copy()
    df["Monto_Limpio"] = pd.to_numeric(df[col_monto], errors="coerce").fillna(0).abs().round(2)
    df["Fecha_Limpia"] = pd.to_datetime(df[col_fecha], format="mixed", dayfirst=True, errors="coerce").dt.date
    df = df.dropna(subset=["Fecha_Limpia"]).reset_index(drop=True)
    df[f"_id_{prefijo_id}"] = df.index
    return df


def conciliar_dos_fuentes(
    df_banco,
    df_auxiliar,
    col_monto_banco,
    col_fecha_banco,
    col_monto_aux,
    col_fecha_aux,
    tolerancia_monto=0.50,
    tolerancia_dias=3,
):
    """
    Concilia dos DataFrames (ej. Banco vs Auxiliar) por monto y fecha,
    usando match exacto primero y aproximado 1-a-1 después.

    Devuelve un dict con:
      - conciliados: DataFrame con las partidas emparejadas (exactas + aproximadas)
      - pendientes_banco: filas de df_banco sin pareja
      - pendientes_auxiliar: filas de df_auxiliar sin pareja
      - resumen: dict con sumas y conteos útiles para el dashboard
    """
    df_b = _preparar(df_banco, col_monto_banco, col_fecha_banco, "banco")
    df_a = _preparar(df_auxiliar, col_monto_aux, col_fecha_aux, "aux")

    # --- Paso 1: match exacto (fecha + monto), soportando duplicados 1 a 1 ---
    df_b["_ocurrencia"] = df_b.groupby(["Fecha_Limpia", "Monto_Limpio"]).cumcount()
    df_a["_ocurrencia"] = df_a.groupby(["Fecha_Limpia", "Monto_Limpio"]).cumcount()

    exactos = pd.merge(
        df_b, df_a,
        on=["Fecha_Limpia", "Monto_Limpio", "_ocurrencia"],
        how="inner",
        suffixes=("_Banco", "_Auxiliar"),
    )
    ids_b_usados = set(exactos["_id_banco"])
    ids_a_usados = set(exactos["_id_aux"])
    # Fecha_Limpia y Monto_Limpio son las claves del merge, así que pandas
    # NO les agrega sufijo (solo lo agrega a columnas repetidas que no son
    # clave). Los recreamos explícitamente con sufijo para que el resultado
    # tenga la misma forma que el bloque de matches aproximados.
    exactos["Fecha_Limpia_Banco"] = exactos["Fecha_Limpia"]
    exactos["Fecha_Limpia_Auxiliar"] = exactos["Fecha_Limpia"]
    exactos["Monto_Limpio_Banco"] = exactos["Monto_Limpio"]
    exactos["Monto_Limpio_Auxiliar"] = exactos["Monto_Limpio"]
    exactos["Tipo_Match"] = "Exacto (fecha + monto)"

    restante_b = df_b[~df_b["_id_banco"].isin(ids_b_usados)].copy()
    restante_a = df_a[~df_a["_id_aux"].isin(ids_a_usados)].copy()

    # --- Paso 2: match aproximado, candidatos por ventana de tolerancia ---
    restante_b_sorted = restante_b.sort_values("Monto_Limpio").reset_index(drop=True)
    restante_a_sorted = restante_a.sort_values("Monto_Limpio").reset_index(drop=True)
    montos_a = restante_a_sorted["Monto_Limpio"].to_numpy()

    candidatos = []
    for _, fila_b in restante_b_sorted.iterrows():
        lo = np.searchsorted(montos_a, fila_b["Monto_Limpio"] - tolerancia_monto, side="left")
        hi = np.searchsorted(montos_a, fila_b["Monto_Limpio"] + tolerancia_monto, side="right")
        if lo >= hi:
            continue
        for j in range(lo, hi):
            fila_a = restante_a_sorted.iloc[j]
            dias_diff = abs((fila_b["Fecha_Limpia"] - fila_a["Fecha_Limpia"]).days)
            if dias_diff <= tolerancia_dias:
                diff_monto = abs(fila_b["Monto_Limpio"] - fila_a["Monto_Limpio"])
                # El monto pesa mucho más que la fecha en el puntaje: preferimos
                # siempre el monto más parecido antes que la fecha más cercana.
                puntaje = diff_monto * 1000 + dias_diff
                candidatos.append((puntaje, fila_b["_id_banco"], fila_a["_id_aux"]))

    candidatos.sort(key=lambda x: x[0])
    usados_b, usados_a = set(), set()
    pares_aprox_ids = []
    for _, id_b, id_a in candidatos:
        if id_b not in usados_b and id_a not in usados_a:
            usados_b.add(id_b)
            usados_a.add(id_a)
            pares_aprox_ids.append((id_b, id_a))

    if pares_aprox_ids:
        ids_b_aprox, ids_a_aprox = zip(*pares_aprox_ids)
        b_por_id = restante_b_sorted.set_index("_id_banco")
        a_por_id = restante_a_sorted.set_index("_id_aux")
        aproximados = pd.concat(
            [
                b_por_id.loc[list(ids_b_aprox)].reset_index(drop=True).add_suffix("_Banco"),
                a_por_id.loc[list(ids_a_aprox)].reset_index(drop=True).add_suffix("_Auxiliar"),
            ],
            axis=1,
        )
        aproximados["Tipo_Match"] = "Aproximado (dentro de tolerancia)"
    else:
        aproximados = pd.DataFrame()

    conciliados = pd.concat([exactos, aproximados], ignore_index=True, sort=False)

    ids_b_final = ids_b_usados | usados_b
    ids_a_final = ids_a_usados | usados_a
    pendientes_banco = df_b[~df_b["_id_banco"].isin(ids_b_final)].drop(
        columns=["Monto_Limpio", "Fecha_Limpia", "_id_banco", "_ocurrencia"], errors="ignore"
    )
    pendientes_auxiliar = df_a[~df_a["_id_aux"].isin(ids_a_final)].drop(
        columns=["Monto_Limpio", "Fecha_Limpia", "_id_aux", "_ocurrencia"], errors="ignore"
    )

    resumen = {
        "suma_conciliado": float(conciliados["Monto_Limpio_Banco"].sum()) if not conciliados.empty else 0.0,
        "suma_banco_pendiente": float(pendientes_banco[col_monto_banco].astype(float).abs().sum()) if not pendientes_banco.empty else 0.0,
        "suma_aux_pendiente": float(pendientes_auxiliar[col_monto_aux].astype(float).abs().sum()) if not pendientes_auxiliar.empty else 0.0,
        "num_exactos": int(len(exactos)),
        "num_aproximados": int(len(aproximados)),
        "num_pendientes_banco": int(len(pendientes_banco)),
        "num_pendientes_auxiliar": int(len(pendientes_auxiliar)),
    }

    return {
        "conciliados": conciliados,
        "pendientes_banco": pendientes_banco,
        "pendientes_auxiliar": pendientes_auxiliar,
        "resumen": resumen,
    }
