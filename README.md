Financial manager 0.0.1

Small and compact back-end rest-api written on flask with jwt auth.  
Also I created Front-end part written on Vue.Js 3.1

Instalation:
## Requirements
This is not ideal code but this is simple solution and practise for use flask, jwt tehnologies

## Instalation:

1. pip3 install -r requirements.txt

## Configuration and setting
2. create and edit simple txt finman_config.json file with next structure:

```json
{
"db_host": "your_db_host",
"db_user": "db_user",
"db_passwd": "db_password",
"db_db": "db_name",
"secret_key": "your_super_secret_key_for_jwt_auth",
"dict_phones":{"+80380501112233":"name1","0631112233":"name2"},
"not_sub_cat":["AliExpress"],
"not_cat":["Грошові перекази"]
}
```

## Create database tables
3. You must execute sqls from sql directory for create working tables:


## Local run
4. python app.app if you run it localy

## Virtual apache shared hosting
5. edit .htaccess file according to your paths



