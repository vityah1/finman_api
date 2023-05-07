from os import environ
import dotenv

dotenv.load_dotenv()

envcfg = {}
envcfg["SECRET_KEY"] = environ["SECRET_KEY"]
envcfg["DATABASE_URI"] = environ["DATABASE_URI"]
