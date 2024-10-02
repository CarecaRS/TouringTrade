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

`email_pwd` é um password específico gerado através do Google, *NÃO É A SENHA DO PRÓPRIO E-MAIL*! Verificar passo a passo, se necessário, em https://support.google.com/accounts/answer/185833. E, sim, tem que utilizar os espaços entre os caracteres.

Também é necessária a liberação por parte da Binance da conexão através do IP atual. Isso é configurado dentro das **Configurações de API** no dashboard da Binance. Se por acaso o provedor de internet fornecer um IP dinâmico (o que é o padrão aqui no Brasil) e a internet cair por qualquer motivo ou faltar luz (pq aí a internet cai), precisa incluir na Binance o novo IP vigente.

Durante duas semanas eu fiquei rodando o Touring através de terminal ("python3 run_touring.py"), a partir de 30/09 19:30 deixei ele rodando em background como service do Arch. Para isso é necessário:
- Arquivo /etc/systemd/system/touring.service contendo:
   ```
  [Unit]
  Description=Touring Personal Crypto Trader
  After=syslog.target network.target
  [Service]
  WorkingDirectory=/home/thiago
  User=thiago
  Environment='PYTHONPATH=/home/thiago/.pyenv/versions/3.12.3/lib/python3.12/site-packages/'
  ExecStart=/usr/bin/run_touring.py
  Restart=always
  [Install]
  WantedBy=multi-user.target
  ```
- Arquivo python `run_touring.py` com permissão de escrita (chmod +x) e copiado para o diretório /usr/bin

O script é rodado em cloud (AWS atualmente - 02/10/2024), de forma muito simples se valendo do comando `nohup`, conforme segue abaixo.

> nohup python3 -u run_touring.py &

O acesso à cloud AWS é feito através de SSH:
> ssh -i 'TouringKeyPair.pem' ubuntu@[endereco].compute.amazonaws.com

O arquivo `TouringKeyPair.pem` e o endereço de acesso (todo o comando para acesso SSH, na realidade) é fornecido pelo sistema da AWS.

O output de cada print realizado pelo sistema (verbose a cada 15min, por exemplo) fica armazenado no arquivo `nohup.out`. Para verificar os últimos movimentos, basta comandar um `tail nohup.out` que o sistema retorna as últimas impressões armazenadas no referido arquivo.

Para o cancelamento do script, busca-se o id do processo com:
> ps aux | grep python3

E então mata-se o processo com `kill [id processo]`.
