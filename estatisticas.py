# Funcoes de estatistica usadas no dashboard
#
# Os dados do Censo de tempo de deslocamento vem agrupados em faixas
# (ate 5 min, 6 a 15 min, ...). Por isso a media e a mediana do tempo sao
# calculadas com as formulas de dados agrupados que vimos em matematica:
#   media   = soma(ponto_medio * frequencia) / total
#   mediana = L + ((n/2 - F_ant) / f_classe) * h

import numpy as np
import pandas as pd

# limites de cada faixa em minutos (a ultima eu fechei em 6h pra conseguir calcular)
FAIXAS_TEMPO = {
    "Até cinco minutos": (0, 5),
    "De seis minutos até quinze minutos": (5, 15),
    "Mais de quinze minutos até meia hora": (15, 30),
    "Mais de meia hora até uma hora": (30, 60),
    "Mais de uma hora até duas horas": (60, 120),
    "Mais de duas horas até quatro horas": (120, 240),
    "Mais de quatro horas": (240, 360),
}

ROTULO_CURTO = {
    "Até cinco minutos": "até 5 min",
    "De seis minutos até quinze minutos": "6 a 15 min",
    "Mais de quinze minutos até meia hora": "15 a 30 min",
    "Mais de meia hora até uma hora": "30 min a 1h",
    "Mais de uma hora até duas horas": "1h a 2h",
    "Mais de duas horas até quatro horas": "2h a 4h",
    "Mais de quatro horas": "mais de 4h",
}


def _ordenar_faixas(freq):
    """recebe uma Series indexada pela faixa e devolve na ordem certa"""
    freq = freq.groupby(level=0).sum()  # junta faixas repetidas (quando soma varias UFs)
    ordem = [f for f in FAIXAS_TEMPO if f in freq.index]
    return freq.reindex(ordem).fillna(0)


def media_agrupada(freq):
    freq = _ordenar_faixas(freq)
    total = freq.sum()
    if total == 0:
        return np.nan
    pontos_medios = np.array([(FAIXAS_TEMPO[f][0] + FAIXAS_TEMPO[f][1]) / 2 for f in freq.index])
    return float((pontos_medios * freq.values).sum() / total)


def quantil_agrupado(freq, p):
    """quantil p (0.25, 0.5, 0.75) por interpolacao dentro da classe"""
    freq = _ordenar_faixas(freq)
    total = freq.sum()
    if total == 0:
        return np.nan
    alvo = total * p
    acumulado = 0
    for faixa, f in freq.items():
        if f > 0 and acumulado + f >= alvo:
            L, sup = FAIXAS_TEMPO[faixa]
            h = sup - L
            return float(L + (alvo - acumulado) / f * h)
        acumulado += f
    return float(list(FAIXAS_TEMPO.values())[-1][1])


def mediana_agrupada(freq):
    return quantil_agrupado(freq, 0.5)


def desvio_agrupado(freq):
    freq = _ordenar_faixas(freq)
    total = freq.sum()
    if total == 0:
        return np.nan
    pm = np.array([(FAIXAS_TEMPO[f][0] + FAIXAS_TEMPO[f][1]) / 2 for f in freq.index])
    media = (pm * freq.values).sum() / total
    var = (freq.values * (pm - media) ** 2).sum() / total
    return float(np.sqrt(var))


def classe_modal(freq):
    freq = _ordenar_faixas(freq)
    if freq.sum() == 0:
        return "-"
    return ROTULO_CURTO[freq.idxmax()]


def resumo_tempo(freq):
    """todas as medidas do tempo de deslocamento de uma vez"""
    q1 = quantil_agrupado(freq, 0.25)
    q3 = quantil_agrupado(freq, 0.75)
    return {
        "media": media_agrupada(freq),
        "mediana": mediana_agrupada(freq),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "desvio": desvio_agrupado(freq),
        "moda": classe_modal(freq),
    }


def resumo_serie(valores):
    """estatistica descritiva 'normal' de uma lista de valores
    (uso pra comparar UFs / municipios entre si)"""
    s = pd.Series(valores).dropna().astype(float)
    if s.empty:
        return None
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    moda = s.round(1).mode()
    return {
        "n": len(s),
        "media": s.mean(),
        "mediana": s.median(),
        "moda": moda.iloc[0] if not moda.empty else np.nan,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "minimo": s.min(),
        "maximo": s.max(),
        "amplitude": s.max() - s.min(),
        "variancia": s.var(ddof=1) if len(s) > 1 else 0.0,
        "desvio": s.std(ddof=1) if len(s) > 1 else 0.0,
        "lim_inf": lim_inf,
        "lim_sup": lim_sup,
    }


def outliers(df, coluna):
    """regra do 1,5 x IQR"""
    r = resumo_serie(df[coluna])
    if r is None:
        return df.iloc[0:0]
    return df[(df[coluna] < r["lim_inf"]) | (df[coluna] > r["lim_sup"])]
