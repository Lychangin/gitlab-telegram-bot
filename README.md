## Gitlab telegram bot  

*This bot get webhook from gitlab ci server and notification users and group about status build*

Structure project

`gitlab-telegram-bot`

`├── README.md`

`├── bot.py`

`├── config.yml`

`├── gitlab-telegram-bot.service`

`├── gitlab.py`

`├── project.json`

`├── project.py`






config.yml - configuration for bot

| Parametr            | Required | Description                              |
| ------------------- | -------- | ---------------------------------------- |
| webhook_host        | Yes      | Hostname server for web hook (external name or ip) |
| webhook_port        | Yes      | Port listener webhooks (available  **443, 80, 88, 8443**) |
| cert                | Yes      | Type certificate (self-signed or official) |
| webhook_ssl_cert    | Yes      | Public certificate                       |
| webhook_ssl_private | No       | Private certificate (if self-signed then you must specify) |
| bot_token           | Yes      | Token telegram bot                       |

Example configuration

```
webhook_host: 'gitlab.ru'
webhook_port: '8443'
cert: 'self-signed' #self-signed or official
webhook_ssl_cert: 'pub.pem' #if official then empty
webhook_ssl_private: 'private-self.key' #if official then empty
bot_token: '436479303:AAGMHWiir9gSU1VWbSe1-PGTIHogjjLcKlw'
```

##### Step-by-Step

```Bash
git clone git@github.com:Lychangin/gitlab-telegram-bot.git

cd gitlab-telegram-bot/

cp gitlab-telegram-bot.service /usr/lib/systemd/system/gitlab-telegram-bot.service

Create self-signed certificate

Example:

openssl req -newkey rsa:2048 -sha256 -nodes -keyout priv-self.key -x509 -days 365 -out pub.pem  
Common Name (e.g. server FQDN or YOUR name) must be your external ip or DNS

Edit config.yml

systemctl daemon-reload

systemctl start gitlab-telegram-bot.service
```





