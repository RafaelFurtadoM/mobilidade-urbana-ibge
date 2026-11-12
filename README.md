# Transporte e Mobilidade Urbana – Censo 2022 (IBGE)

Parte individual do Projeto Integrador **"Números que Falam – Descobrindo o Brasil"** (Python + Matemática).

Indicador: **5. Transporte e Mobilidade Urbana**

Personas: Fernando (Secretário Nacional de Mobilidade Urbana), Ana (Gestora de Transportes da RM de Goiânia),
Luciene (Prefeita de Vitória), Pedrinho (Prefeito de Belo Horizonte) e Lucas (Especialista em Logística de Brasília).

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Os dados já estão na pasta `dados/`. Se quiser baixar de novo direto do IBGE:

```bash
python preparar_dados.py
```

## Estrutura

```
app.py              -> dashboard em Streamlit
estatisticas.py     -> funções de média, mediana, quartis, IQR, desvio padrão e outliers
preparar_dados.py   -> baixa as tabelas da API do SIDRA e salva em CSV (ETL)
dados/              -> bases do IBGE já tratadas
imagens/            -> fotos usadas na seção de notícias (Wikimedia Commons)
```

## Dados usados (IBGE – Censo Demográfico 2022, SIDRA)

| Tabela | O que tem |
|---|---|
| [10330](https://sidra.ibge.gov.br/tabela/10330) | tempo de deslocamento × meio de transporte × cor ou raça (Brasil, UFs e capitais) |
| [10331](https://sidra.ibge.gov.br/tabela/10331) | tempo de deslocamento × cor ou raça × renda domiciliar per capita |
| [10332](https://sidra.ibge.gov.br/tabela/10332) | meio de transporte por município (para o ranking de bicicleta) |

O meio de transporte do Censo é aquele em que a pessoa **passa mais tempo** no caminho até o trabalho.

## O que tem no dashboard

- **Barra lateral:** upload de CSV/XLSX, filtro de Região, UF, Região Metropolitana (capital), meio de transporte, cor ou raça e renda.
- **Visão geral:** KPIs de % coletivo / particular / ativo, gráfico de rosca do modal predominante e barras por raça.
- **Mediana por raça (KPI):** mediana do tempo de deslocamento para cada cor/raça, mapa de calor meio × raça e tabela com média, mediana, Q1, Q3, IQR, desvio padrão e classe modal.
- **Gargalos e outliers:** boxplot do tempo por meio de transporte comparando UFs ou capitais, com média, mediana, moda, quartis, IQR, amplitude, variância, desvio padrão e lista de outliers (regra 1,5·IQR).
- **Renda:** tempo de deslocamento e % que leva mais de 1h por faixa de renda e raça.
- **Mobilidade ativa:** ranking das cidades com mais uso de bicicleta, boxplot entre municípios e tabela das capitais.
- **Notícias:** reportagens sobre caos no trânsito e mobilidade, com fotos.

## Como calculei as estatísticas

O IBGE divulga o tempo de deslocamento em **faixas** (até 5 min, 6 a 15 min, 15 a 30 min...), então não dá pra
usar `mean()` direto. Usei as fórmulas de dados agrupados:

- **Média:** soma de (ponto médio da faixa × frequência) ÷ total
- **Mediana e quartis:** `Md = L + ((n/2 − F) / f) · h`, onde L é o limite inferior da classe da mediana,
  F é a frequência acumulada antes dela, f é a frequência da classe e h é a amplitude da classe
- **Desvio padrão:** raiz da média dos quadrados das distâncias dos pontos médios até a média
- A última faixa ("mais de 4 horas") eu fechei em 6 horas pra conseguir calcular

Para comparar UFs, capitais e municípios entre si (boxplot) usei a estatística normal com pandas
(`quantile`, `std`, `var`) e a regra **Q1 − 1,5·IQR / Q3 + 1,5·IQR** pra achar os outliers.

## Respostas às perguntas de negócio (Brasil)

**1. Qual é a mediana por meio de transporte por raça?**

Mediana do tempo até o trabalho (minutos):

| Meio | Branca | Preta | Parda | Amarela | Indígena | Geral |
|---|---|---|---|---|---|---|
| A pé | 10,6 | 14,0 | 12,5 | 9,6 | 12,9 | 11,9 |
| Bicicleta | 16,5 | 20,0 | 18,5 | 16,2 | 20,2 | 18,1 |
| Motocicleta | 14,7 | 17,5 | 15,8 | 14,6 | 16,2 | 15,6 |
| Automóvel | 17,8 | 22,2 | 20,2 | 20,5 | 20,9 | 19,0 |
| Ônibus | 43,3 | 48,1 | 46,1 | 44,3 | 46,2 | 45,4 |
| Trem ou metrô | 57,5 | 71,7 | 70,1 | 46,5 | 62,5 | 63,5 |
| **Todos** | **19,6** | **25,0** | **21,9** | **21,2** | **20,3** | **21,2** |

Pessoas pretas levam em média 5,4 minutos a mais que pessoas brancas (mediana). A diferença aparece em todos os
meios de transporte, até no trem/metrô (14 minutos a mais), o que mostra que a população preta e parda mora mais
longe dos lugares de trabalho.

**2. Qual a porcentagem que usa transporte público, particular ou ativo?**

- Particular (carro, moto, táxi, mototáxi): **~50%** (só o carro é 31,8%)
- Coletivo (ônibus, BRT, trem/metrô, van, barco): **~24,5%** (ônibus é 20,8%)
- Ativo (a pé e bicicleta): **~24%** (a pé 17,7% e bicicleta 6,2%)

Por raça muda bastante: 42% dos brancos vão de carro, contra 20,5% dos pretos. Entre os pretos o ônibus é o
principal meio (28,8%) e entre os indígenas é a pé (32,9%).

**3. Quais cidades têm mais mobilidade ativa (bicicleta)?**

Entre municípios com pelo menos 20 mil trabalhadores: Ubatuba-SP (38,1%), Pirapora-MG (32,4%), Capanema-PA (31%),
Peruíbe-SP (31%), Janaúba-MG (29,4%), Lorena-SP, Itanhaém-SP, Caraguatatuba-SP, São Sebastião-SP e Guarujá-SP.
A mediana dos municípios é só 4,7%, e a média (7,1%) é maior por causa desses outliers: a distribuição é
assimétrica à direita.

## Gargalos encontrados

- As capitais com maior mediana de tempo são **São Paulo (41 min)**, **Rio de Janeiro (39 min)** e Salvador (36 min).
  Brasília (29 min) e Belo Horizonte (30 min) também ficam acima da maioria.
- Entre as UFs, Rio de Janeiro (31 min) e Distrito Federal (29 min) se destacam no topo do boxplot.
- Quanto menor a renda, maior o tempo: até 1/2 salário mínimo per capita, 13,5% levam mais de 1 hora;
  acima de 5 salários, só 8,8%.

## Recomendações para as personas

- **Fernando (nacional):** priorizar investimento em transporte coletivo de alta capacidade nas metrópoles
  onde trem/metrô e ônibus passam de 1 hora (SP, RJ, DF), que é onde a população preta e parda mais perde tempo.
- **Ana (Goiânia):** 66% dos deslocamentos em Goiânia são por carro/moto e só 17% por coletivo. Melhorar o BRT
  e os corredores de ônibus ajuda a tirar carros da rua.
- **Luciene (Vitória) e Pedrinho (BH):** BH está entre as capitais mais lentas; vale olhar o boxplot por capital
  e a tabela de capitais pra comparar com cidades de mesmo porte.
- **Lucas (Brasília):** o DF aparece como outlier de tempo entre as UFs, o que pesa na logística de entregas e
  no trajeto dos trabalhadores das cidades-satélite.

## Fontes

- IBGE – Censo Demográfico 2022, SIDRA (tabelas 10330, 10331, 10332)
- Fotos: Wikimedia Commons (créditos na aba Notícias do dashboard)
