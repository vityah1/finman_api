from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app import create_app

app = create_app()

if __name__ == '__main__':
    uvicorn.run("runserver:app", host='0.0.0.0', port=8090, reload=True)
