# TouringTrade
TouringTrade is a personal assistant (a.k.a. 'bot') that buys and sell cryptocurrency.

I made it to trade using Binance API (`python-binance` package in Python) for a few specific reasons:
- 24/7 trading (no open/close hours, so one is not subject to the oscillations worldwide between closing and opening);
- Minimal values for trading;
- Low trading costs (0,1%).

## Requisites
A file `keys.py` must be created beforehand by the user and it must be in the same directory as the main file `touring.py`. `keys.py` ought to have a few parameters:
- api_key = 'foo'
- api_secret = 'bar'
- email_sender = 'anything@anywhere.com'
- email_personal = 'your_email@gmail.com' # yeap, must be Gmail
- email_pwd = 'abcd abcd abcd abcd'

The API key and API secret are generated in Binance user page (Account > API Management). For obvious reasons mine are not present in this repository. Also, your keys won't be just 'foo' and/or 'bar', they are strings of many characters.

The object `email_sender` in theory would be used as, well, the e-mail sender, but my tests with Gmail indicate that this information is useless: the e-mails happen to be received (and sent) as the user himself (through `email_personal` object).

`email_personal` refers to the user personal e-mail, which will receive the buy/sell/report notifications.

`email_pwd` is a specific password created through Google, *IT'S NOT THE E-MAIL PASSWORD ITSELF*! Check step by step, if necessary, in https://support.google.com/accounts/answer/185833. And yes, the spaces between the characters have to be used.

It is also needed the confirmation by Binance for the conection through your actual IP. This is configurated at **API Management / [edit restrictions]** in Binance dashboard. If your internet provider gives you a dynamic IP (which is the standard here in Brasil) and your internet signal happens to be down for whatever reason then you must include your new running IP in Binance too.

The script can run over the cloud (I used AWS for about six months), and it's as easy as it gets: just use command `nohup`, as follows:

> nohup python3 -u run_touring.py &

AWS cloud access is done through SSH:
> ssh -i 'TouringKeyPair.pem' ubuntu@[address].compute.amazonaws.com

The file `TouringKeyPair.pem` and the access address (the whole SSH command, actually) are informed by the AWS system.

Each print output (verbose every 15min, for example) is stored in the file `nohup.out`. To check the last movements, just input a `tail nohup.out` and the system gives you the last few lines stored in the aforementioned file.

To interrupt the script, one needs to fetch the process id with:
> ps aux | grep python3

And then just kill the procecss with `kill [process id]`.
