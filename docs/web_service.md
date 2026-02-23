## 정보

- 홈페이지: http://alphacrafter.wonbbo.kro.kr/
- NginX 설정: /etc/nginx/conf.d/flask_app.conf
- Gunicorn 설정: /etc/systemd/system/flask_app.service

## 체크

- 서비스로 운영되는 웹
  - sudo systemctl [start, stop, restart, status] [service name]

- 웹서비스 오류 체크
  - sudo systemctl status flask_app
- 웹서비스 nginx
  - sudo systemctl status nginx

```bash

sudo vi /etc/systemd/system/algoforge-api.service
sudo vi /etc/systemd/system/algoforge-web.service

sudo systemctl daemon-reload
sudo systemctl enable algoforge-api
sudo systemctl enable algoforge-web

sudo systemctl start algoforge-api
sudo systemctl restart algoforge-api
sudo systemctl status algoforge-api

sudo systemctl start algoforge-web
sudo systemctl restart algoforge-web
sudo systemctl status algoforge-web

sudo journalctl -u algoforge-api -f
sudo journalctl -u algoforge-web -f

# Nginx 로그
sudo tail -f /var/log/nginx/algoforge_access.log
sudo tail -f /var/log/nginx/algoforge_error.log

```
