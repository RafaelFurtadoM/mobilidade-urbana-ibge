# Dashboard - Transporte e Mobilidade Urbana (Censo 2022 / IBGE)
# Projeto Integrador Python + Matematica - parte individual
#
# rodar: streamlit run app.py

import os
import pandas as pd
import plotly.express as px
import streamlit as st

import estatisticas as est

st.set_page_config(page_title="Mobilidade Urbana - IBGE", page_icon="🚌", layout="wide")

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA, "dados")

REGIOES = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}

SIGLAS = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

# como eu agrupei os meios de transporte pra responder a pergunta
# "publico x particular x ativo"
GRUPO_MEIO = {
    "Ônibus": "Coletivo (ônibus/metrô)",
    "BRT ou ônibus de trânsito rápido": "Coletivo (ônibus/metrô)",
    "Trem ou metrô": "Coletivo (ônibus/metrô)",
    "Van, perua ou assemelhados": "Coletivo (ônibus/metrô)",
    "Embarcação de médio e grande porte (acima de 20 pessoas)": "Coletivo (ônibus/metrô)",
    "Automóvel": "Particular (carro/moto)",
    "Motocicleta": "Particular (carro/moto)",
    "Táxi ou assemelhados": "Particular (carro/moto)",
    "Mototáxi": "Particular (carro/moto)",
    "A pé": "Ativo (bicicleta/a pé)",
    "Bicicleta": "Ativo (bicicleta/a pé)",
}

# nomes menores pra caber nos graficos
NOME_CURTO = {
    "BRT ou ônibus de trânsito rápido": "BRT",
    "Van, perua ou assemelhados": "Van/perua",
    "Caminhonete ou caminhão adaptado (pau de arara)": "Pau de arara",
    "Embarcação de médio e grande porte (acima de 20 pessoas)": "Barco grande",
    "Embarcação de pequeno porte (até 20 pessoas)": "Barco pequeno",
    "Táxi ou assemelhados": "Táxi/app",
}

ORDEM_RENDA = [
    "Sem rendimento", "Até 1/4 de salário mínimo", "Mais de 1/4 a 1/2 salário mínimo",
    "Mais de 1/2 a 1 salário mínimo", "Mais de 1 a 2 salários mínimos",
    "Mais de 2 a 3 salários mínimos", "Mais de 3 a 5 salários mínimos", "Mais de 5 salários mínimos",
]

CORES_RACA = {"Branca": "#4C78A8", "Preta": "#E45756", "Parda": "#F58518",
              "Amarela": "#EECA3B", "Indígena": "#54A24B"}


# ------------------------------------------------------------------
# carregamento e tratamento dos dados
# ------------------------------------------------------------------

def ler_arquivo(arq):
    nome = arq.name if hasattr(arq, "name") else str(arq)
    if nome.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(arq)
    else:
        df = pd.read_csv(arq, sep=None, engine="python", encoding="utf-8")
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def tratar(df):
    df = df.copy()
    df["cod_local"] = df["cod_local"].astype(str).str.replace(".0", "", regex=False)
    df["pessoas"] = pd.to_numeric(df["pessoas"], errors="coerce").fillna(0)
    df["regiao"] = df["cod_local"].str[0].map(REGIOES)
    df["cod_uf"] = df["cod_local"].str[:2]
    df["uf"] = df["cod_uf"].map(SIGLAS)
    for col in ["tempo", "meio_transporte", "raca", "renda"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df


def identificar(df):
    """descobre qual das 3 bases e pelo nome das colunas"""
    cols = set(df.columns)
    if {"tempo", "meio_transporte", "raca"} <= cols:
        return "tempo_meio_raca"
    if {"tempo", "raca", "renda"} <= cols:
        return "tempo_raca_renda"
    if {"meio_transporte", "pessoas"} <= cols and "tempo" not in cols:
        return "meio_municipios"
    return None


@st.cache_data
def carregar_padrao():
    bases = {}
    for nome in ["tempo_meio_raca", "tempo_raca_renda", "meio_municipios"]:
        bases[nome] = tratar(ler_arquivo(os.path.join(PASTA_DADOS, nome + ".csv")))
    return bases


bases = carregar_padrao()

# ------------------------------------------------------------------
# barra lateral
# ------------------------------------------------------------------

st.sidebar.title("🚦 Filtros")

with st.sidebar.expander("📂 Enviar dados do IBGE (CSV/XLSX)"):
    st.caption("Use arquivos com as mesmas colunas da pasta dados/ "
               "(gerados pelo preparar_dados.py a partir do SIDRA).")
    enviados = st.file_uploader("Arquivos", type=["csv", "xlsx"], accept_multiple_files=True)
    for arq in enviados or []:
        try:
            df_novo = ler_arquivo(arq)
            tipo = identificar(df_novo)
            if tipo is None:
                st.error(f"{arq.name}: não reconheci as colunas")
            else:
                bases[tipo] = tratar(df_novo)
                st.success(f"{arq.name} carregado como '{tipo}'")
        except Exception as erro:
            st.error(f"Erro ao ler {arq.name}: {erro}")

tmr = bases["tempo_meio_raca"]
trr = bases["tempo_raca_renda"]
mun = bases["meio_municipios"]

regioes_sel = st.sidebar.multiselect("Região", list(REGIOES.values()), default=list(REGIOES.values()))

ufs_disp = sorted(tmr[(tmr["nivel"] == "N3") & (tmr["regiao"].isin(regioes_sel))]["uf"].dropna().unique())
ufs_sel = st.sidebar.multiselect("UF (vazio = todas da região)", ufs_disp)
if not ufs_sel:
    ufs_sel = ufs_disp

capitais = tmr[(tmr["nivel"] == "N6") & (tmr["uf"].isin(ufs_sel))]["local"].drop_duplicates().sort_values()
capital_sel = st.sidebar.selectbox("Região metropolitana (capital)",
                                   ["Todas (somar as UFs)"] + list(capitais))

meios_todos = [m for m in tmr["meio_transporte"].unique() if m != "Total"]
meios_sel = st.sidebar.multiselect("Meio de transporte", meios_todos, default=meios_todos)

racas_todas = [r for r in tmr["raca"].unique() if r != "Total"]
racas_sel = st.sidebar.multiselect("Cor ou raça", racas_todas, default=racas_todas)

rendas_todas = [r for r in ORDEM_RENDA if r in trr["renda"].unique()]
rendas_sel = st.sidebar.multiselect("Categoria de renda (per capita)", rendas_todas, default=rendas_todas)

st.sidebar.markdown("---")
st.sidebar.caption("Fonte: IBGE, Censo Demográfico 2022 - tabelas SIDRA 10330, 10331 e 10332.")

if not meios_sel or not racas_sel or not ufs_sel:
    st.warning("Selecione pelo menos uma opção em cada filtro.")
    st.stop()


def recorte(df):
    """aplica o filtro territorial: uma capital ou a soma das UFs escolhidas"""
    if capital_sel.startswith("Todas"):
        return df[(df["nivel"] == "N3") & (df["uf"].isin(ufs_sel))]
    return df[(df["nivel"] == "N6") & (df["local"] == capital_sel)]


nome_recorte = capital_sel if not capital_sel.startswith("Todas") else (
    "Brasil" if len(ufs_sel) == 27 else ", ".join(ufs_sel))

# base filtrada que vai ser usada em quase tudo
base = recorte(tmr)
base = base[base["meio_transporte"].isin(meios_sel) & base["raca"].isin(racas_sel)]
base_faixas = base[base["tempo"] != "Total"]
base_total = base[base["tempo"] == "Total"]

# ------------------------------------------------------------------
# cabecalho
# ------------------------------------------------------------------

st.title("🚌 Transporte e Mobilidade Urbana no Brasil")
st.markdown(
    "**Startup de análise de dados** · Relatório para Fernando (Secretário Nacional de Mobilidade), "
    "Ana (RM de Goiânia), Luciene (Vitória), Pedrinho (Belo Horizonte) e Lucas (logística, Brasília)."
)
st.caption(f"Recorte atual: **{nome_recorte}** · {len(meios_sel)} meio(s) de transporte · "
           f"{len(racas_sel)} grupo(s) de cor/raça")

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Visão geral", "⏱️ Mediana por raça (KPI)", "🚧 Gargalos e outliers",
    "💰 Renda", "🚲 Mobilidade ativa", "📰 Notícias",
])

# ------------------------------------------------------------------
# ABA 1 - visao geral
# ------------------------------------------------------------------
with aba1:
    total = base_total["pessoas"].sum()
    por_meio = base_total.groupby("meio_transporte")["pessoas"].sum().sort_values(ascending=False)
    por_grupo = base_total.assign(grupo=base_total["meio_transporte"].map(GRUPO_MEIO).fillna("Outros")) \
        .groupby("grupo")["pessoas"].sum()
    pct = (por_grupo / total * 100) if total else por_grupo * 0
    freq_geral = base_faixas.groupby("tempo")["pessoas"].sum()
    r_geral = est.resumo_tempo(freq_geral)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Trabalhadores que se deslocam", f"{total/1e6:.2f} mi" if total > 1e6 else f"{total:,.0f}".replace(",", "."))
    c2.metric("🚌 Coletivo", f"{pct.get('Coletivo (ônibus/metrô)', 0):.1f}%")
    c3.metric("🚗 Particular", f"{pct.get('Particular (carro/moto)', 0):.1f}%")
    c4.metric("🚶 Ativo", f"{pct.get('Ativo (bicicleta/a pé)', 0):.1f}%")
    c5.metric("Mediana do tempo", f"{r_geral['mediana']:.1f} min")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Modal predominante")
        detalhado = st.toggle("Mostrar cada meio separado", value=False)
        if detalhado:
            dados_pizza = por_meio.rename(index=lambda m: NOME_CURTO.get(m, m)).reset_index()
            dados_pizza.columns = ["meio", "pessoas"]
        else:
            dados_pizza = por_grupo.reset_index()
            dados_pizza.columns = ["meio", "pessoas"]
        fig = px.pie(dados_pizza, names="meio", values="pessoas", hole=0.5)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")

    with col_b:
        st.subheader("Meio de transporte por cor ou raça (%)")
        tab_raca = base_total.groupby(["raca", "meio_transporte"])["pessoas"].sum().reset_index()
        tab_raca["%"] = tab_raca["pessoas"] / tab_raca.groupby("raca")["pessoas"].transform("sum") * 100
        tab_raca["meio"] = tab_raca["meio_transporte"].map(lambda m: NOME_CURTO.get(m, m))
        principais = por_meio.head(6).index
        tab_raca = tab_raca[tab_raca["meio_transporte"].isin(principais)]
        fig = px.bar(tab_raca, x="raca", y="%", color="meio", barmode="group",
                     labels={"raca": "Cor ou raça", "%": "% dos trabalhadores", "meio": "Meio"})
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    if total:
        mais_usado = por_meio.index[0]
        st.info(
            f"📌 **Leitura:** em {nome_recorte}, o meio mais usado é **{mais_usado}** "
            f"({por_meio.iloc[0]/total*100:.1f}% dos trabalhadores). "
            f"O transporte coletivo responde por {pct.get('Coletivo (ônibus/metrô)', 0):.1f}%, "
            f"o particular por {pct.get('Particular (carro/moto)', 0):.1f}% e o ativo por "
            f"{pct.get('Ativo (bicicleta/a pé)', 0):.1f}%. No gráfico ao lado dá pra ver que "
            "pessoas brancas usam muito mais o carro, enquanto pretos e pardos dependem mais do ônibus e de andar a pé."
        )

# ------------------------------------------------------------------
# ABA 2 - mediana do tempo por meio e por raca
# ------------------------------------------------------------------
with aba2:
    st.subheader("Mediana do tempo de deslocamento por cor ou raça")
    st.caption("O Censo divulga o tempo em faixas, então a mediana foi calculada por interpolação "
               "(fórmula de dados agrupados): Md = L + ((n/2 − F) / f) · h")

    cols = st.columns(len(racas_sel))
    resumo_racas = {}
    for col, raca in zip(cols, racas_sel):
        freq = base_faixas[base_faixas["raca"] == raca].groupby("tempo")["pessoas"].sum()
        r = est.resumo_tempo(freq)
        resumo_racas[raca] = r
        delta = r["mediana"] - r_geral["mediana"]
        col.metric(raca, f"{r['mediana']:.1f} min", f"{delta:+.1f} min vs. geral", delta_color="inverse")

    st.markdown("#### Mediana (min) por meio de transporte × cor ou raça")
    linhas = []
    for (meio, raca), g in base_faixas.groupby(["meio_transporte", "raca"]):
        linhas.append({"Meio": NOME_CURTO.get(meio, meio), "Raça": raca,
                       "Mediana": est.mediana_agrupada(g.set_index("tempo")["pessoas"])})
    matriz = pd.DataFrame(linhas).pivot(index="Meio", columns="Raça", values="Mediana")
    fig = px.imshow(matriz.round(1), text_auto=True, aspect="auto", color_continuous_scale="OrRd",
                    labels=dict(color="minutos"))
    fig.update_layout(height=520, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

    st.markdown("#### Todas as medidas por cor ou raça")
    tabela = pd.DataFrame(resumo_racas).T
    tabela = tabela.rename(columns={"media": "Média", "mediana": "Mediana", "q1": "Q1", "q3": "Q3",
                                    "iqr": "IQR", "desvio": "Desvio padrão", "moda": "Classe modal"})
    st.dataframe(tabela.style.format({c: "{:.1f}" for c in tabela.columns if c != "Classe modal"}),
                 width="stretch")

    if "Branca" in resumo_racas and "Preta" in resumo_racas:
        dif = resumo_racas["Preta"]["mediana"] - resumo_racas["Branca"]["mediana"]
        st.info(
            f"📌 **Leitura:** no recorte escolhido, a mediana das pessoas pretas é "
            f"{dif:.1f} min {'maior' if dif > 0 else 'menor'} que a das pessoas brancas. "
            "Mesmo usando o mesmo meio (ex.: trem/metrô ou ônibus), pretos e pardos demoram mais, "
            "o que indica que moram mais longe dos centros de emprego. A média fica acima da mediana "
            "porque poucas pessoas com viagens de 2h ou mais puxam a média pra cima."
        )

# ------------------------------------------------------------------
# ABA 3 - boxplot / outliers
# ------------------------------------------------------------------
with aba3:
    st.subheader("Onde estão os gargalos? Boxplot do tempo de deslocamento")
    nivel = st.radio("Comparar entre:", ["UFs", "Capitais"], horizontal=True)
    nv = "N3" if nivel == "UFs" else "N6"

    dados_nv = tmr[(tmr["nivel"] == nv) & (tmr["uf"].isin(ufs_sel)) & (tmr["tempo"] != "Total")
                   & (tmr["meio_transporte"].isin(meios_sel)) & (tmr["raca"].isin(racas_sel))]

    # deixo so os meios mais usados pra nao poluir o grafico
    principais = (base_total.groupby("meio_transporte")["pessoas"].sum()
                  .sort_values(ascending=False).head(6).index)
    linhas = []
    for (local, meio), g in dados_nv[dados_nv["meio_transporte"].isin(principais)].groupby(["local", "meio_transporte"]):
        freq = g.groupby("tempo")["pessoas"].sum()
        if freq.sum() < 200:  # pouca gente, a mediana fica instavel
            continue
        linhas.append({"local": local, "meio": NOME_CURTO.get(meio, meio),
                       "mediana_min": est.mediana_agrupada(freq),
                       "pct_mais_1h": freq[[f for f in freq.index if "uma hora até" in f or "duas horas" in f
                                            or "quatro horas" in f]].sum() / freq.sum() * 100})
    terr = pd.DataFrame(linhas)

    if terr.empty:
        st.warning("Sem dados suficientes para esse filtro.")
    else:
        fig = px.box(terr, x="meio", y="mediana_min", points="all", hover_name="local",
                     labels={"meio": "Meio de transporte", "mediana_min": "Mediana do tempo (min)"})
        fig.update_layout(height=480, margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

        meio_foco = st.selectbox("Estatísticas detalhadas do meio:", sorted(terr["meio"].unique()),
                                 index=sorted(terr["meio"].unique()).index("Ônibus")
                                 if "Ônibus" in terr["meio"].unique() else 0)
        foco = terr[terr["meio"] == meio_foco]
        r = est.resumo_serie(foco["mediana_min"])
        k = st.columns(4)
        k[0].metric("Média", f"{r['media']:.1f} min")
        k[1].metric("Mediana", f"{r['mediana']:.1f} min")
        k[2].metric("IQR (Q3 − Q1)", f"{r['iqr']:.1f} min")
        k[3].metric("Desvio padrão", f"{r['desvio']:.1f} min")
        k = st.columns(4)
        k[0].metric("Q1 / Q3", f"{r['q1']:.1f} / {r['q3']:.1f}")
        k[1].metric("Amplitude", f"{r['amplitude']:.1f} min")
        k[2].metric("Variância", f"{r['variancia']:.1f}")
        k[3].metric("Moda", f"{r['moda']:.1f} min")

        outs = est.outliers(foco, "mediana_min").sort_values("mediana_min", ascending=False)
        st.markdown(f"**Outliers (regra 1,5·IQR):** limite inferior {r['lim_inf']:.1f} min, "
                    f"limite superior {r['lim_sup']:.1f} min")
        if outs.empty:
            st.write("Nenhum outlier para esse meio no recorte escolhido.")
        else:
            st.dataframe(outs[["local", "mediana_min", "pct_mais_1h"]].rename(columns={
                "local": nivel[:-1], "mediana_min": "Mediana (min)", "pct_mais_1h": "% com mais de 1h"}),
                hide_index=True, width="stretch")

        st.markdown(f"#### % de trabalhadores que levam mais de 1 hora ({meio_foco})")
        fig = px.bar(foco.sort_values("pct_mais_1h", ascending=False).head(15),
                     x="local", y="pct_mais_1h",
                     labels={"local": "", "pct_mais_1h": "% com mais de 1h"})
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

        mais_lento = foco.sort_values("mediana_min", ascending=False).iloc[0]
        texto_out = (f"Os outliers são: {', '.join(outs['local'])}. " if not outs.empty
                     else "Não apareceu outlier, mas o lugar mais lento é "
                          f"{mais_lento['local']} ({mais_lento['mediana_min']:.1f} min). ")
        st.info(
            f"📌 **Leitura:** a média ({r['media']:.1f} min) e a mediana ({r['mediana']:.1f} min) "
            f"{'estão próximas' if abs(r['media'] - r['mediana']) < 2 else 'são diferentes'}. "
            + texto_out +
            "Valores muito altos puxam a média pra cima, por isso a mediana é a medida mais justa pra comparar. "
            "Os pontos acima da caixa são os gargalos: lugares onde o trabalhador gasta bem mais tempo que o normal."
        )

# ------------------------------------------------------------------
# ABA 4 - renda
# ------------------------------------------------------------------
with aba4:
    st.subheader("Tempo de deslocamento por renda domiciliar per capita")
    st.caption("Tabela 10331 do SIDRA (não tem o meio de transporte, por isso o filtro de meio não se aplica aqui).")
    br = recorte(trr)
    br = br[br["raca"].isin(racas_sel) & br["renda"].isin(rendas_sel) & (br["tempo"] != "Total")]

    linhas = []
    for (renda, raca), g in br.groupby(["renda", "raca"]):
        freq = g.groupby("tempo")["pessoas"].sum()
        mais1h = freq[[f for f in freq.index if "uma hora até" in f or "duas horas" in f
                       or "quatro horas" in f]].sum()
        linhas.append({"renda": renda, "raca": raca, "mediana": est.mediana_agrupada(freq),
                       "pct_mais_1h": mais1h / freq.sum() * 100 if freq.sum() else 0})
    tab_renda = pd.DataFrame(linhas)
    if tab_renda.empty:
        st.warning("Sem dados para esse filtro.")
    else:
        ordem = [r for r in ORDEM_RENDA if r in rendas_sel]
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(tab_renda, x="renda", y="mediana", color="raca", barmode="group",
                         category_orders={"renda": ordem}, color_discrete_map=CORES_RACA,
                         labels={"renda": "Renda per capita", "mediana": "Mediana (min)", "raca": "Raça"})
            fig.update_layout(title="Mediana do tempo (min)", margin=dict(t=40))
            st.plotly_chart(fig, width="stretch")
        with c2:
            fig = px.line(tab_renda, x="renda", y="pct_mais_1h", color="raca", markers=True,
                          category_orders={"renda": ordem}, color_discrete_map=CORES_RACA,
                          labels={"renda": "Renda per capita", "pct_mais_1h": "% com mais de 1h", "raca": "Raça"})
            fig.update_layout(title="% que leva mais de 1 hora", margin=dict(t=40))
            st.plotly_chart(fig, width="stretch")

        st.info(
            "📌 **Leitura:** quanto menor a renda, maior o tempo no trajeto. No Brasil, quem ganha até 1/2 salário "
            "mínimo per capita tem mediana em torno de 23 min e cerca de 13,5% leva mais de 1 hora; acima de "
            "5 salários a mediana cai pra uns 19 min e só 8,8% passa de 1 hora. Quem tem menos renda mora mais "
            "longe do trabalho e depende de ônibus/trem, enquanto a renda alta usa carro e mora perto dos centros. "
            "Em todas as faixas, pretos e pardos aparecem com tempos maiores que brancos."
        )

# ------------------------------------------------------------------
# ABA 5 - bicicleta
# ------------------------------------------------------------------
with aba5:
    st.subheader("Quais cidades têm mais mobilidade ativa (bicicleta)?")
    m = mun[mun["uf"].isin(ufs_sel)].pivot_table(index=["local", "uf"], columns="meio_transporte",
                                                  values="pessoas", aggfunc="sum").reset_index()
    m["% bicicleta"] = m["Bicicleta"] / m["Total"] * 100
    m["% a pé"] = m["A pé"] / m["Total"] * 100
    m["% ativo"] = m["% bicicleta"] + m["% a pé"]

    minimo = st.slider("Mínimo de trabalhadores no município (pra tirar cidades muito pequenas)",
                       0, 200000, 20000, step=5000)
    m_f = m[m["Total"] >= minimo]

    c1, c2 = st.columns([3, 2])
    with c1:
        top = m_f.sort_values("% bicicleta", ascending=False).head(15)
        fig = px.bar(top.sort_values("% bicicleta"), x="% bicicleta", y="local", orientation="h",
                     text=top.sort_values("% bicicleta")["% bicicleta"].round(1),
                     labels={"local": "", "% bicicleta": "% dos trabalhadores que vão de bicicleta"})
        fig.update_layout(height=520, margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.box(m_f, y="% bicicleta", points="outliers", hover_name="local",
                     labels={"% bicicleta": "% bicicleta por município"})
        fig.update_layout(height=520, margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    r = est.resumo_serie(m_f["% bicicleta"])
    if r:
        k = st.columns(6)
        k[0].metric("Municípios", r["n"])
        k[1].metric("Média", f"{r['media']:.1f}%")
        k[2].metric("Mediana", f"{r['mediana']:.1f}%")
        k[3].metric("IQR", f"{r['iqr']:.1f} p.p.")
        k[4].metric("Desvio padrão", f"{r['desvio']:.1f} p.p.")
        k[5].metric("Amplitude", f"{r['amplitude']:.1f} p.p.")
        n_out = len(est.outliers(m_f, "% bicicleta"))
        st.info(
            f"📌 **Leitura:** a média ({r['media']:.1f}%) é maior que a mediana ({r['mediana']:.1f}%), "
            f"ou seja, a distribuição é assimétrica à direita. Existem {n_out} municípios outliers "
            f"(acima de {r['lim_sup']:.1f}%), quase todos cidades planas do litoral paulista, norte de Minas e Pará, "
            "onde a bicicleta é o transporte do dia a dia. Nas capitais o uso é bem menor."
        )

    st.markdown("#### Capitais (personas)")
    caps = tmr[(tmr["nivel"] == "N6") & (tmr["tempo"] == "Total") & (tmr["raca"] == "Total")]
    caps = caps.pivot_table(index="local", columns="meio_transporte", values="pessoas", aggfunc="sum")
    caps = pd.DataFrame({
        "% bicicleta": caps["Bicicleta"] / caps["Total"] * 100,
        "% a pé": caps["A pé"] / caps["Total"] * 100,
        "% ônibus/BRT/metrô": (caps["Ônibus"] + caps["BRT ou ônibus de trânsito rápido"] + caps["Trem ou metrô"]) / caps["Total"] * 100,
        "% carro": caps["Automóvel"] / caps["Total"] * 100,
    }).round(1).sort_values("% bicicleta", ascending=False)
    personas = ["Goiânia (GO)", "Vitória (ES)", "Belo Horizonte (MG)", "Brasília (DF)"]
    st.dataframe(caps.style.apply(
        lambda linha: ["background-color: #fff3cd" if linha.name in personas else "" for _ in linha], axis=1),
        width="stretch", height=400)
    st.caption("Em amarelo: cidades das personas do cenário.")

# ------------------------------------------------------------------
# ABA 6 - noticias
# ------------------------------------------------------------------
with aba6:
    st.subheader("Caos no trânsito e mobilidade sustentável")

    noticias = [
        {
            "img": os.path.join(PASTA, "imagens", "brt_rio.jpg"),
            "titulo": "Censo inédito dos deslocamentos mostra necessidade de BRTs metropolitanos",
            "fonte": "Diário do Transporte (dez/2025)",
            "link": "https://diariodotransporte.com.br/2025/12/14/inedito-censo-dos-deslocamentos-do-ibge-pela-primeira-vez-mostra-a-necessidade-de-brts-metropolitanos-menos-usados-que-pau-de-arara-e-mototaxis/",
            "credito": "Foto: Mario Roberto Durán Ortiz / Wikimedia Commons (CC BY-SA 3.0)",
        },
        {
            "img": os.path.join(PASTA, "imagens", "move_bh.jpg"),
            "titulo": "Automóvel é o meio de transporte mais utilizado no deslocamento para o trabalho",
            "fonte": "Agência IBGE Notícias",
            "link": "https://agenciadenoticias.ibge.gov.br/agencia-noticias/noticias/44713-automovel-e-o-meio-de-transporte-mais-utilizado-no-deslocamento-para-o-trabalho",
            "credito": "Foto: Ladislau Fernandes / Wikimedia Commons (CC BY-SA 4.0)",
        },
        {
            "img": os.path.join(PASTA, "imagens", "metro_sp.jpg"),
            "titulo": "1,3 milhão de brasileiros levam mais de duas horas para chegar ao trabalho",
            "fonte": "InfoMoney",
            "link": "https://www.infomoney.com.br/brasil/13-milhao-de-brasileiros-levam-mais-de-duas-horas-para-chegar-ao-trabalho-diz-ibge/",
            "credito": "Foto: Wilfredor / Wikimedia Commons (CC BY-SA 4.0)",
        },
        {
            "img": os.path.join(PASTA, "imagens", "eixo_brasilia.jpg"),
            "titulo": "Ônibus lotado e horas no caminho: o drama de quem vai ou volta do trabalho",
            "fonte": "Diário do Pará",
            "link": "https://diariodopara.com.br/noticias/brasil/onibus-lotado-e-horas-no-caminho-o-drama-de-quem-vai-ou-volta-do-trabalho/",
            "credito": "Foto: Cayambe / Wikimedia Commons (CC BY-SA 3.0)",
        },
        {
            "img": os.path.join(PASTA, "imagens", "ciclovia_paulista.jpg"),
            "titulo": "Quase metade das mulheres leva mais de uma hora para chegar ao trabalho em algumas cidades",
            "fonte": "Portal do Trânsito",
            "link": "https://www.portaldotransito.com.br/noticias/mobilidade-e-tecnologia/mobilidade-urbana/quase-metade-das-mulheres-leva-mais-de-uma-hora-para-chegar-ao-trabalho-em-algumas-cidades-brasileiras/",
            "credito": "Foto: Marcelo Camargo / Agência Brasil (CC BY 3.0 BR)",
        },
        {
            "img": None,
            "titulo": "Santo André–São Paulo é o maior deslocamento metropolitano; ônibus é o coletivo mais importante",
            "fonte": "Diário do Transporte (out/2025)",
            "link": "https://diariodotransporte.com.br/2025/10/09/ibge-santo-andre-a-sao-paulo-e-o-maior-deslocamento-metropolitano-maioria-usa-carro-no-pais-e-onibus-e-o-meio-de-transporte-coletivo-mais-importante-diz-censo/",
            "credito": "",
        },
    ]

    colunas = st.columns(3)
    for i, n in enumerate(noticias):
        with colunas[i % 3]:
            with st.container(border=True):
                if n["img"] and os.path.exists(n["img"]):
                    st.image(n["img"], width="stretch")
                st.markdown(f"**{n['titulo']}**")
                st.caption(n["fonte"])
                st.link_button("Ler reportagem", n["link"])
                if n["credito"]:
                    st.caption(n["credito"])

with st.expander("ℹ️ Sobre os dados e a metodologia"):
    st.markdown("""
- **Fonte:** IBGE – Censo Demográfico 2022, resultados de deslocamento para o trabalho (SIDRA).
  - Tabela **10330**: tempo de deslocamento × meio de transporte × cor ou raça (pessoas que voltam pra casa 3+ dias por semana).
  - Tabela **10331**: tempo de deslocamento × cor ou raça × renda domiciliar per capita.
  - Tabela **10332**: meio de transporte por município (usada no ranking de bicicleta).
- O "meio de transporte" é aquele em que a pessoa **passa mais tempo** no trajeto.
- O tempo vem em faixas. Para média, mediana e quartis usei as fórmulas de **dados agrupados**
  (ponto médio da classe e interpolação). A última faixa ("mais de 4 horas") foi fechada em 6 horas.
- Outliers: valores abaixo de Q1 − 1,5·IQR ou acima de Q3 + 1,5·IQR.
- Grupos: **coletivo** = ônibus, BRT, trem/metrô, van e barco grande; **particular** = carro, moto, táxi e mototáxi;
  **ativo** = a pé e bicicleta.
""")
