from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from enum import Enum
import requests
import os
import csv
import json
from pathlib import Path
import ssl
import certifi

# Configurações iniciais
BEARER_TOKEN = "zQwcy2podAfPPYeoqtrdwvbECb5BbIyr7Xa9KYftTdJhrbxHpPPo09Ol1oWvKIzx"
DOWNLOAD_DIR = "downloads"
TIMEOUT = 20  # Timeout para requests em segundos

# Criando diretório de downloads, se não existir
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configuração para uso do SSL com certificados
ssl_context = ssl.create_default_context(cafile=certifi.where())

class CategoriaEnum(str, Enum):
    producao = "producao"
    processamento = "processamento"
    comercializacao = "comercializacao"
    importacao = "importacao"
    exportacao = "exportacao"

CATEGORIA_URLS = {
    CategoriaEnum.producao: "http://vitibrasil.cnpuv.embrapa.br/download/Producao.csv",
    CategoriaEnum.processamento: "http://vitibrasil.cnpuv.embrapa.br/download/ProcessaViniferas.csv",
    CategoriaEnum.comercializacao: "http://vitibrasil.cnpuv.embrapa.br/download/Comercio.csv",
    CategoriaEnum.importacao: "http://vitibrasil.cnpuv.embrapa.br/download/ImpVinhos.csv",
    CategoriaEnum.exportacao: "http://vitibrasil.cnpuv.embrapa.br/download/ExpVinho.csv",
}

app = FastAPI()
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

@app.get("/embrapa/vitivinicultura/")
def get_categoria(
    categoria: CategoriaEnum = Query(..., description="Categoria de dados para consulta"),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
):
    file_path = Path(DOWNLOAD_DIR) / f"{categoria.value}.csv"

    # Verifica se o arquivo já existe
    if file_path.exists():
        return csv_to_json(file_path)

    # Faz o download do arquivo, se necessário
    url = CATEGORIA_URLS.get(categoria)
    try:
        response = requests.get(url, timeout=TIMEOUT, verify=ssl_context)
        response.raise_for_status()

        # Salva o arquivo no diretório de downloads
        with open(file_path, "wb") as file:
            file.write(response.content)

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail={"error": 500, "message": str(e)})

    # Retorna o conteúdo do arquivo como JSON
    return csv_to_json(file_path)

def csv_to_json(file_path):
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=';')
            rows = [row for row in reader]
            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": 500, "message": f"Error reading CSV file: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
