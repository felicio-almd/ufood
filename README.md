# ufood


## Para rodar
```bash
git clone https://github.com/felicio-almd/ufood.git

cd ufood

cp .env.example .env 

(muda as variaveis de ambiente)

docker build -t ufes-menu-scraper .

docker run --rm --env-file /projetos/ufood/.env ufes-menu-scraper
```

Depois basta configurar o cronjob que desejar para executar da forma que quiser