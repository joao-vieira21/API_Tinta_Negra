from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API Tinta Negra",
    description="""
API para integração com Google Sheets.

Permite envio (POST) e consulta (GET) de dados de forma simples,
pensada para integração com microcontroladores (ESP32) e sistemas externos.
"""
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

google_key = os.getenv("GOOGLE_KEY")
if not google_key:
    raise ValueError("GOOGLE_KEY não encontrada")

key = json.loads(google_key)

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN não encontrado")

scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(key, scopes=scopes)
client = gspread.authorize(creds)

planilha_completa = client.open(
    title="monitor_temp",
    folder_id="1xntTqkJ_jnZfvRpB3y5fHqyuOs5fxWr_"
)

aba = planilha_completa.get_worksheet(0)

def nova_linha(ID, data, hora, temperatura, potencia):
    proxima_row = len(aba.get_all_values()) + 1
    aba.update(
        f"A{proxima_row}:E{proxima_row}",
        [[ID, data, hora, temperatura, potencia]]
    )

class Leitura(BaseModel):
    ID: str
    data: str
    hora: str
    temperatura: float
    potencia: float
    token: str

@app.get("/")
def raiz():
    return {"status": "ok"}

@app.get("/lersheets")
def ler_todas(validacao_token: str = Header()):

    if validacao_token != token:
        raise HTTPException(status_code=401, detail="Acesso negado")

    return aba.get_all_records()

@app.post("/nova-leitura")
def receber_leitura(leitura: Leitura):
    if leitura.token != token:
        raise HTTPException(status_code=401, detail="Acesso negado")

    nova_linha(
        leitura.ID,
        leitura.data,
        leitura.hora,
        leitura.temperatura,
        leitura.potencia
    )

    return {"status": "ok"}

