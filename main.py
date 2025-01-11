from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from enum import Enum
from typing import List
import requests
import os
import csv
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
ssl_context = certifi.where()

class CategoriaEnum(str, Enum):
    producao = "producao"
    comercializacao = "comercializacao"
    processamento = "processamento"
    importacao = "importacao"
    exportacao = "exportacao"

CATEGORIA_URLS = {
    CategoriaEnum.producao: "http://vitibrasil.cnpuv.embrapa.br/download/Producao.csv",
    CategoriaEnum.comercializacao: "http://vitibrasil.cnpuv.embrapa.br/download/Comercio.csv",
    CategoriaEnum.processamento: [
        {"Vinífera": "http://vitibrasil.cnpuv.embrapa.br/download/ProcessaViniferas.csv"},
        {"Sem Classe": "http://vitibrasil.cnpuv.embrapa.br/download/ProcessaSemclass.csv"},
        {"Mesa": "http://vitibrasil.cnpuv.embrapa.br/download/ProcessaMesa.csv"},
        {"Americanas": "http://vitibrasil.cnpuv.embrapa.br/download/ProcessaAmericanas.csv"}
    ],
    CategoriaEnum.importacao: [
      {"Vinhos": "http://vitibrasil.cnpuv.embrapa.br/download/ImpVinhos.csv"},
      {"Sucos":"http://vitibrasil.cnpuv.embrapa.br/download/ImpSuco.csv"},
      {"Passas":"http://vitibrasil.cnpuv.embrapa.br/download/ImpPassas.csv"},
      {"Frescas":"http://vitibrasil.cnpuv.embrapa.br/download/ImpFrescas.csv"},
      {"Espumantes":"http://vitibrasil.cnpuv.embrapa.br/download/ImpEspumantes.csv"}
    ],
    CategoriaEnum.exportacao: [
        {"Vinhos":"http://vitibrasil.cnpuv.embrapa.br/download/ExpVinho.csv"},
        {"Sucos":"http://vitibrasil.cnpuv.embrapa.br/download/ExpSuco.csv"},
        {"Uvas":"http://vitibrasil.cnpuv.embrapa.br/download/ExpUva.csv"},
        {"Espumantes":"http://vitibrasil.cnpuv.embrapa.br/download/ExpEspumantes.csv"}
    ],
}

app = FastAPI()
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

@app.get(
    "/embrapa/vitivinicultura/{categoria}",
    responses={
        200: {"description": "Lista de dados categorizados"},
        500: {"description": "Erro interno de servidor"},
    },
)
def get_categoria(
    categoria: CategoriaEnum,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
):
    urls = CATEGORIA_URLS.get(categoria)

    if not urls:
        raise HTTPException(status_code=404, detail=f"Categoria '{categoria}' não encontrada.")

    if isinstance(urls, str):  # Categoria simples
        file_path = download_file(urls, categoria.value)
        return csv_to_json(file_path)

    elif isinstance(urls, list):  # Categoria com múltiplos arquivos
        all_data = []
        for url_obj in urls:
            for key, url in url_obj.items():  # Itera pela chave (ex.: "Vinífera") e URL
                file_path = download_file(url, f"{categoria.value}_{key}")
                all_data.extend(csv_to_json(file_path))
        return all_data

    raise HTTPException(status_code=500, detail="Erro interno desconhecido.")

def download_file(url: str, filename: str) -> Path:
    file_path = Path(DOWNLOAD_DIR) / f"{filename}.csv"
    if file_path.exists():
        return file_path

    try:
        response = requests.get(url, timeout=TIMEOUT, verify=ssl_context)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail={"error": 500, "message": str(e)})

    return file_path

def csv_to_json(file_path: Path) -> List[dict]:
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=";")
            rows = []

            for row in reader:
                json_row = {}
                anos = {}
                for key, value in row.items():
                    if key.isdigit():
                        if key not in anos:
                            anos[key] = {"quantidade": value}
                        else:
                            anos[key]["valor"] = value
                    else:
                        json_row[key] = value
                if anos:
                    json_row["anos"] = anos
                rows.append(json_row)

            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": 500, "message": f"Error reading CSV file: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)