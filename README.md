# TouringTrade
TouringTrade is a personal assistant (a.k.a. 'bot') that I made from scratch, it buys and sells cryptocurrency through Binance.

I made it using Binance API (`python-binance` package in Python) for a few specific reasons:
- 24/7 trading (no open/close hours, so one is not subject to the oscillations worldwide between closing and opening);
- Minimal values for trading;
- Low trading costs (0,1%).

If someone wants to work with another exchange or make it so that Touring can trade other assets (stocks, options, whatever), the solution is very simple, it just needs a little tweak in the code and you're done. For each desired asset or exchange, the user must read the proprer documentation with the service or asset provider.


## The files
TouringTrade has three key files, one has the sole purpose of backtesting strategies with real on-line data, the other two are used for the trade itself and for the activities record. Another file is created for logging, as stated deep down in this README.

`backtest_touring.py` is the backtest script, `touring.py` is the trading script and `livro_contabil.csv` (portuguese for 'ledger') is the, well, ledger that records all buy and sell trades, amount traded, dates and so on. The details about how the scripts work are registered inside each script, also, of course, how one is able to create his own strategies for buying/selling crypto.


## Requisites
A file `keys.py` must be created beforehand by the user and it must be in the same directory as the main file `touring.py`. `keys.py` must have a few parameters:
- api_key = 'foo'
- api_secret = 'bar'
- email_sender = 'anyone@anywhere.com'
- email_personal = 'your_email@gmail.com' # yeap, must be Gmail
- email_pwd = 'abcd abcd abcd abcd'

The API key and API secret are generated in Binance user page (Account > API Management). For obvious reasons mine are not present in this repository. Also, your keys won't be just 'foo' and/or 'bar', they are strings of many characters.

The object `email_sender` in theory would be used as, well, the e-mail sender, but my tests with Gmail indicate that this information is useless: the e-mails happen to be received (and sent) as the user himself (through `email_personal` object).

`email_personal` refers to the user personal e-mail, which will receive the buy/sell/report notifications.

`email_pwd` is a specific password created through Google, *IT'S NOT THE E-MAIL PASSWORD ITSELF*! Check step by step, if necessary, in https://support.google.com/accounts/answer/185833. And yes, the spaces between the characters have to be used.

It is also needed the confirmation by Binance for the conection through your actual IP. This is configurated at **API Management / [edit restrictions]** in Binance dashboard. If your internet provider gives you a dynamic IP (which is the standard here in Brasil) and your internet signal happens to be down for whatever reason then you must include your new running IP in Binance too.


## Running the personal assistant

One can run it in a personal computer or laptop, also the script can run over the cloud (I used AWS for about six months, free of charges), and it's as easy as it gets: just use command `nohup`, as follows.

> nohup python3 -u run_touring.py &

AWS cloud access is done through SSH:
> ssh -i 'TouringKeyPair.pem' ubuntu@[address].compute.amazonaws.com

The file `TouringKeyPair.pem` and the access address (the whole SSH command, actually) are informed by the AWS system.

Each print output (verbose every 15min, for example) is stored in the file `nohup.out`. To check the last movements, just input a `tail nohup.out` and the system gives you the last few lines stored in the aforementioned file.

To interrupt the script, one needs to fetch the process id with:
> ps aux | grep python3

And then just kill the procecss with `kill [process id]`.
