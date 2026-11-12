# Baixa as tabelas do Censo 2022 (deslocamento para o trabalho) direto da API do SIDRA
# e salva em CSV na pasta dados/
#
# Tabelas usadas:
#   10330 - tempo de deslocamento x meio de transporte x cor ou raca
#   10331 - tempo de deslocamento x cor ou raca x renda domiciliar per capita
#   10332 - meio de transporte x cor ou raca (usei so por municipio, pra ver bicicleta)
#
# rodar: python preparar_dados.py

import os
import time
import requests
import pandas as pd

API = "https://servicodados.ibge.gov.br/api/v3/agregados"
PASTA = "dados"

# codigos IBGE das capitais (pra ter o recorte por cidade / regiao metropolitana)
CAPITAIS = {
    "1100205": "Porto Velho", "1200401": "Rio Branco", "1302603": "Manaus",
    "1400100": "Boa Vista", "1501402": "Belém", "1600303": "Macapá",
    "1721000": "Palmas", "2111300": "São Luís", "2211001": "Teresina",
    "2304400": "Fortaleza", "2408102": "Natal", "2507507": "João Pessoa",
    "2611606": "Recife", "2704302": "Maceió", "2800308": "Aracaju",
    "2927408": "Salvador", "3106200": "Belo Horizonte", "3205309": "Vitória",
    "3304557": "Rio de Janeiro", "3550308": "São Paulo", "4106902": "Curitiba",
    "4205407": "Florianópolis", "4314902": "Porto Alegre", "5002704": "Campo Grande",
    "5103403": "Cuiabá", "5208707": "Goiânia", "5300108": "Brasília",
}


def baixar(tabela, variavel, localidades, classificacao):
    url = f"{API}/{tabela}/periodos/2022/variaveis/{variavel}"
    params = {"localidades": localidades, "classificacao": classificacao}
    for tentativa in range(3):
        try:
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print("  erro, tentando de novo...", e)
            time.sleep(3)
    raise RuntimeError(f"nao consegui baixar a tabela {tabela}")


def json_para_df(dados):
    """A API devolve um json bem aninhado, aqui eu transformo em tabela"""
    linhas = []
    for var in dados:
        for res in var["resultados"]:
            cats = {}
            for c in res["classificacoes"]:
                nome_col = c["nome"]
                cats[nome_col] = list(c["categoria"].values())[0]
            for serie in res["series"]:
                linha = dict(cats)
                linha["cod_local"] = serie["localidade"]["id"]
                linha["local"] = serie["localidade"]["nome"]
                linha["nivel"] = serie["localidade"]["nivel"]["id"]
                linha["valor"] = serie["serie"]["2022"]
                linhas.append(linha)
    df = pd.DataFrame(linhas)
    # o IBGE usa "-" pra zero e "X" pra dado sigiloso
    df["valor"] = pd.to_numeric(df["valor"].replace({"-": 0, "X": None, "...": None}), errors="coerce")
    return df


def renomear(df):
    return df.rename(columns={
        "Tempo habitual de deslocamento do domicílio para o trabalho principal": "tempo",
        "Meio de transporte em que passa mais tempo para chegar ao local de trabalho": "meio_transporte",
        "Cor ou raça": "raca",
        "Classes de rendimento nominal mensal domiciliar per capita": "renda",
        "Local de exercício do trabalho principal": "local_trabalho",
        "Nível de instrução": "instrucao",
        "Sexo": "sexo",
        "valor": "pessoas",
    })


def main():
    os.makedirs(PASTA, exist_ok=True)
    capitais = ",".join(CAPITAIS.keys())

    print("Tabela 10330 (tempo x meio x raca) - Brasil, UFs e capitais")
    d = baixar(10330, 13376, f"N1[all]|N3[all]|N6[{capitais}]",
               "537[all]|2088[all]|86[all]|469[79176]")
    df = renomear(json_para_df(d)).drop(columns=["local_trabalho"])
    df.to_csv(f"{PASTA}/tempo_meio_raca.csv", index=False, encoding="utf-8")
    print("  ", len(df), "linhas")

    print("Tabela 10331 (tempo x raca x renda) - Brasil, UFs e capitais")
    d = baixar(10331, 13556, f"N1[all]|N3[all]|N6[{capitais}]",
               "537[all]|2[6794]|86[all]|386[all]")
    df = renomear(json_para_df(d)).drop(columns=["sexo"])
    df.to_csv(f"{PASTA}/tempo_raca_renda.csv", index=False, encoding="utf-8")
    print("  ", len(df), "linhas")

    print("Tabela 10332 (meio de transporte) - todos os municipios")
    # total, a pe, bicicleta, moto, carro e onibus (todos os meios estoura o limite da API)
    partes = []
    codigos_uf = [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                  31, 32, 33, 35, 41, 42, 43, 50, 51, 52, 53]
    for uf in codigos_uf:
        print("   UF", uf)
        d = baixar(10332, 13377, f"N6[N3[{uf}]]",
                   "2088[79488,79193,79194,79195,79197,79208]|1568[120704]|86[95251]")
        partes.append(json_para_df(d))
    df = renomear(pd.concat(partes)).drop(columns=["instrucao", "raca"])
    df.to_csv(f"{PASTA}/meio_municipios.csv", index=False, encoding="utf-8")
    print("  ", len(df), "linhas")

    print("pronto!")


if __name__ == "__main__":
    main()
