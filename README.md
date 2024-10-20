Financial manager 0.0.2

Small and compact back-end rest-api written on flask with jwt auth.  
Also I created Front-end part written on Vue.Js 3.1

Installation:
## Requirements
This is not ideal code but this is simple solution and practise for use flask, jwt technologies

## 1. Installation:

pip3 install -r requirements.txt

## 2. Configuration and setting
Create and edit simple txt .env file with next data:

```
DATABASE_URI = mysql+pymysql://user:password@host:post/database
SECRET_KEY = your_super_secret_string
```

## 3. Local run
python app.app if you run it locally

## 4. For virtual apache shared hosting only
Edit .htaccess file according to your paths

## setup as service

create file finman.service: 

```
[Unit]
Description=Gunicorn to serv finman
After=network.target

[Service]
#User=finamn
Group=finman
WorkingDirectory=/home/finman/finman_api
ExecStart=/bin/bash -c "source /home/finman/finman_api/venv/bin/activate && gunicorn -w 2 -b 127.0.0.1:8090 app:app"

[Install]
#WantedBy=multi-user.target
WantedBy=default.target
```

cp finman.service /etc/systemd/system/finman.service

```
sudo systemctl daemon-reload
systemctl start finman
systemctl enable finman
```

## Docker

docker compose up -d

## 5. Init database

`
flask db init
flask db migrate -m "Initial migration"
`

for init with existing tables use next command:
`flask db revision --autogenerate -m "Initial migration"`

`flask db upgrade`

## Setup alembic env.py to keep  service or history tables

add next function:
```python
def include_object(object, name: str, type_, reflected, compare_to):
    """
    Should you include this table or not?
    """

    if type_ == 'table' and (name.startswith('_') or object.info.get("skip_autogenerate", False)):
        return False

    elif type_ == "column" and object.info.get("skip_autogenerate", False):
        return False

    return True
```

add next row with this function:
```python
target_metadata=get_metadata(),
include_object=include_object,
```