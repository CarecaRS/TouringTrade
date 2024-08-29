# TouringTrade
O TouringTrade é um assistente pessoal (a.k.a. 'bot') de compra/venda de ativos.

O desenvolvimento inicial é feito utilizando a Binance (pacote `python-binance` no Python) em função de alguns motivos principais:
- Possibilidade de negociação 24/7 (não tem abertura/fechamento de pregão, refém das oscilações que ocorrem entre o fechamento e abertura);
- Valores mínimos para poder realizar um trade;
- Baixo custo de corretagem (0%).

## Requisitos
O arquivo `keys.py` deve estar na mesma pasta do arquivo principal `touring.py`, contendo apenas dois parâmetros:
- api_key = 'foo'
- api_secret = 'bar'

As chaves API e API Secret são geradas/informadas no site da Binance, na página do usuário (Conta > Gerenciamento de API). Pelo óbvio, não está presente neste repositório o meu arquivo particular contendo as minhas chaves. Também é elementar que as chaves são strings complexas e não apenas 'foo' e/ou 'bar'.
