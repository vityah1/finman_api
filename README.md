Small and compact back-end rest-api for front-end Vue.Js 3.1 financial manger writen flask and using jwt auth

Instalation:

1. pip3 install -r requirements.txt

2. create and edit simple txt func.json file with next structur: 
{
"db_host": "your_db_host",
"db_user": "db_user",
"db_passwd": "db_password",
"db_db": "db_name",
"secret_key": "your_super_secret_key_for_jwt_auth"
}
3. You must execute sqls from sql directory for create working tables:

# for local run
4. python app.app if you run it localy

# for virtual apache shared hosting
5. edit .htaccess file with your directories
6. main.py


