#!/home/vityah1/kt.if.ua/mypy/gapi/bin/python3.6
from wsgiref.handlers import CGIHandler
import os
import sys

sys.path.insert(0, "/home/vityah1/kt.if.ua/mypy/gapi/lib/python3.6/site-packages")
# sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

try:
    from app import app
except Exception as e:
    print("Content-Type:application/json;charset=utf-8\n\n")
    print(f"""error during import app from app: {e}""")


# from yourapplication import app


class ScriptNameStripper(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        os.environ["SCRIPT_NAME"] = ""
        return self.app(environ, start_response)


app = ScriptNameStripper(app)
CGIHandler().run(app)
