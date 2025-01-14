# Embrapa Vitivinicultura API

Esta aplicação é uma API FastAPI que permite acessar informações de produção, processamento, comercialização, importação e exportação de vinhos e uvas da Embrapa.

## Requisitos

- **Python 3.14 ou superior**
- **Git instalado**

## Como executar

### 1. Clone o repositório

Execute o seguinte comando no terminal:
```bash
   git clone https://github.com/rodrigorizandobr/fiap-tech-challenge-1.git
   cd fiap-tech-challenge-1
```

### 2. Configure o ambiente virtual e inicie a aplicação

#### **Para macOS/Linux:**
```bash
python3 -m venv env && source venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload
```

#### **Para Windows (PowerShell):**
```powershell
python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt; uvicorn main:app --reload
```

### 3. Acesse a API

- **Documentação interativa:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Exemplo de chamada cURL:**
   ```bash
   curl -X GET "http://127.0.0.1:8000/embrapa/vitivinicultura/producao" -H "Authorization: Bearer zQwcy2podAfPPYeoqtrdwvbECb5BbIyr7Xa9KYftTdJhrbxHpPPo09Ol1oWvKIzx"
   ```

---

## Como desligar a aplicação

1. Pressione `CTRL+C` no terminal onde a aplicação está rodando para interromper a execução.
2. **Para desativar o ambiente virtual:**
   - **macOS/Linux ou Windows (PowerShell):**
     ```bash
     deactivate
     ```

---

## Como apagar o ambiente virtual

1. Certifique-se de que o ambiente virtual está desativado.
2. Apague o diretório `venv`:
   - **macOS/Linux:**
     ```bash
     rm -rf venv
     ```
   - **Windows (PowerShell):**
     ```powershell
     Remove-Item -Recurse -Force venv
     ```

---

## Estrutura do Projeto

- **`main.py`:** Código principal da aplicação.
- **`requirements.txt`:** Dependências do projeto.

---

## Observações

- Certifique-se de que a porta `8000` esteja disponível no seu sistema.
- Se desejar alterar o token Bearer ou URLs, edite diretamente o arquivo `main.py`.
