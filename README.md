# TouringTrade
O TouringTrade é um assistente pessoal (a.k.a. 'bot') de compra/venda de ativos.

O desenvolvimento inicial é feito utilizando a Binance (pacote `python-binance` no Python) em função de alguns motivos principais:
- Possibilidade de negociação 24/7 (não tem abertura/fechamento de pregão, refém das oscilações que ocorrem entre o fechamento e abertura);
- Valores mínimos para poder realizar um trade;
- Baixo custo de corretagem (0,1%).

## Requisitos
Um arquivo `keys.py` deve ser criado pelo usuário e estar na mesma pasta do arquivo principal `touring.py`, contendo alguns parâmetros:
- api_key = 'foo'
- api_secret = 'bar'
- email_sender = 'quem_envia@qualquercoisa.com'
- email_personal = 'email_particular_da_pessoa@gmail.com'
- email_pwd = 'abcd abcd abcd abcd'

As chaves API e API Secret são geradas/informadas no site da Binance, na página do usuário (Conta > Gerenciamento de API). Pelo óbvio, não está presente neste repositório o meu arquivo particular contendo as minhas chaves. Também é elementar que as chaves são strings complexas e não apenas 'foo' e/ou 'bar'.

O objeto `email_sender` seria para utilizar como remetente, mas nos meus testes (utilizando o Gmail) essa informação é desprezível. O e-mail acaba sendo recebido como eu enviando para mim mesmo.

`email_personal` refere-se ao e-mail do usuário, que receberá as notificações de compra/venda.

`email_pwd` é um password específico gerado através do Google, *NÃO É A SENHA DO PRÓPRIO E-MAIL*! Verificar passo a passo, se necessário, em https://support.google.com/accounts/answer/185833
