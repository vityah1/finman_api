Financial manager 0.0.1

Small and compact back-end rest-api written on flask with jwt auth.  
Also I created Front-end part written on Vue.Js 3.1

Instalation:
## Requirements
This is not ideal code but this is simple solution and practise for use flask, jwt tehnologies

## Instalation:

1. pip3 install -r requirements.txt

## Configuration and setting
2. create and edit simple txt .env file with next data:

```
DATABASE_URI = mysql+pymysql://user:password@host:post/database
SECRET_KEY = your_super_secret_string
```

## Local run
4. python app.app if you run it localy

## Virtual apache shared hosting
5. edit .htaccess file according to your paths

## Init database
6. 
flask db init
flask db migrate -m "Initial migration"
flask db upgrade



