# 🤖 Finance Chat API

API de chatbot financeiro inteligente desenvolvida em Python com FastAPI e Google Gemini.

🔗 **[API em produção](https://finance-chat-api.onrender.com)**

---

## ✨ Funcionalidades

- **Chatbot financeiro** — responde perguntas sobre finanças pessoais
- **Análise personalizada** — considera saldo, transações e categorias do usuário
- **Histórico de conversa** — mantém contexto entre mensagens
- **Integração com IA** — powered by Google Gemini 2.5 Flash

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| [Python 3.12](https://python.org) | Linguagem principal |
| [FastAPI](https://fastapi.tiangolo.com) | Framework web |
| [Google Gemini](https://ai.google.dev) | Modelo de IA |
| [Pydantic](https://docs.pydantic.dev) | Validação de dados |
| [Docker](https://www.docker.com) | Containerização |
| [Render](https://render.com) | Deploy |

---

## 🚀 Como rodar localmente

### Pré-requisitos

- [Python 3.12](https://python.org/downloads)
- Chave da [Google Gemini API](https://aistudio.google.com/apikey)

### Instalação

```bash
git clone https://github.com/cauamconceicao/finance-chat-api.git
cd finance-chat-api
pip install -r requirements.txt
```

Cria o arquivo `.env`:

```env
GEMINI_API_KEY=sua_chave_aqui
```

```bash
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000`

---

## 📋 Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/chat` | Envia mensagem para o chatbot |
| GET | `/health` | Verifica se a API está no ar |

---

## 📝 Exemplo de uso

### Chat

```json
POST https://finance-chat-api.onrender.com/chat
{
  "message": "Estou gastando muito?",
  "transactions": [
    {"title": "Almoço", "amount": 45.00, "category": "Alimentação", "description": "Restaurante"},
    {"title": "Uber", "amount": 30.00, "category": "Transporte", "description": "Corrida"},
    {"title": "Netflix", "amount": 55.90, "category": "Lazer", "description": "Streaming"}
  ],
  "balance": 1500.00,
  "currency": "BRL"
}
```

### Resposta

```json
{
  "response": "Analisando seus dados financeiros, você possui um saldo de R$ 1.500,00...",
  "session_id": "default"
}
```

---

## 🔗 Integração

Esta API foi desenvolvida para integrar com o [FinanceAI](https://financeai-dun.vercel.app) — app de gestão financeira com Open Banking.

---

## 📄 Licença

MIT © [Cauã Conceição](https://github.com/cauamconceicao)