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
import re
from unidecode import unidecode




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
        {"Sucos": "http://vitibrasil.cnpuv.embrapa.br/download/ImpSuco.csv"},
        {"Passas": "http://vitibrasil.cnpuv.embrapa.br/download/ImpPassas.csv"},
        {"Frescas": "http://vitibrasil.cnpuv.embrapa.br/download/ImpFrescas.csv"},
        {"Espumantes": "http://vitibrasil.cnpuv.embrapa.br/download/ImpEspumantes.csv"}
    ],
    CategoriaEnum.exportacao: [
        {"Vinhos": "http://vitibrasil.cnpuv.embrapa.br/download/ExpVinho.csv"},
        {"Sucos": "http://vitibrasil.cnpuv.embrapa.br/download/ExpSuco.csv"},
        {"Uvas": "http://vitibrasil.cnpuv.embrapa.br/download/ExpUva.csv"},
        {"Espumantes": "http://vitibrasil.cnpuv.embrapa.br/download/ExpEspumantes.csv"}
    ],
}

app = FastAPI()
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

@app.get(
    "/embrapa/vitivinicultura/{categoria}",
    responses={
        200: {"descrição": "Lista de dados categorizados"},
        500: {"descrição": "Erro interno de servidor"},
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

def slugify(value: str) -> str:
    """
    Transforma uma string em um slug:
    - Remove acentos.
    - Converte para minúsculas.
    - Substitui espaços e caracteres especiais por '-'.
    """
    value = unidecode(value)  # Remove acentos e normaliza
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()  # Remove caracteres especiais
    value = re.sub(r"[-\s]+", "-", value)  # Substitui espaços e hífens consecutivos por um único hífen
    return value

def download_file(url: str, filename: str) -> Path:
    slug_filename = slugify(filename)
    file_path = Path(DOWNLOAD_DIR) / f"{slug_filename}.csv"
    if file_path.exists():
        return file_path

    try:
        response = requests.get(url, timeout=TIMEOUT, verify=ssl_context)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail={"Erro": 500, "Mensagem": str(e)})

    return file_path

def csv_to_json(file_path: Path) -> List[dict]:
    try:
        # Substituir tabulação por ponto e vírgula antes de processar
        with open(file_path, mode="r", encoding="utf-8") as file:
            content = file.read().replace("\t", ";")
        
        # Reescrevendo o arquivo com o delimitador correto
        with open(file_path, mode="w", encoding="utf-8") as file:
            file.write(content)

        # Agora processa o arquivo
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=';')
            header = next(reader)  # Lê o cabeçalho

            # Identificar anos e mapear 'quantidade' e 'valor'
            years_mapping = {}
            non_year_columns = []
            for index, col in enumerate(header):
                if col.isdigit():  # Coluna de ano
                    if col not in years_mapping:
                        years_mapping[col] = {"valor": index}  # Primeiro valor para o ano
                    else:
                        years_mapping[col]["quantidade"] = index  # Segundo valor para o ano
                else:
                    non_year_columns.append((index, col))  # Colunas que não são anos

            # Processa os dados
            rows = []
            for row in reader:
                json_row = {}
                anos = {}

                # Adiciona colunas não relacionadas a anos
                for index, col_name in non_year_columns:
                    if index < len(row):
                        json_row[col_name] = row[index].strip()

                # Adiciona colunas relacionadas a anos
                for year, indices in years_mapping.items():
                    quantidade = row[indices.get("quantidade", -1)].strip() if "quantidade" in indices else None
                    valor = row[indices["valor"]].strip() if "valor" in indices else None

                    # Preenche apenas `valor` se `quantidade` não estiver presente
                    if quantidade is None or quantidade == "":
                        anos[year] = {"valor": valor}
                    else:
                        anos[year] = {"quantidade": quantidade, "valor": valor}

                json_row["anos"] = anos
                rows.append(json_row)

            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail={"Erro": 500, "Mensagem": f"Erro na leitura do arquivo CSV: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
