import os
import json
from typing import Optional
from contextlib import asynccontextmanager

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# In-memory conversation history keyed by session_id
conversation_sessions: dict[str, list[dict]] = {}

SYSTEM_PROMPT = """Você é um assistente financeiro pessoal inteligente e empático chamado FinBot.
Seu objetivo é ajudar o usuário a entender sua situação financeira, identificar padrões de gastos,
dar dicas de economia e responder perguntas sobre finanças pessoais.

Diretrizes:
- Seja sempre claro, objetivo e amigável
- Use os dados financeiros fornecidos para personalizar suas respostas
- Formate valores monetários com a moeda correta do usuário
- Identifique padrões preocupantes e celebre hábitos positivos
- Sugira ações práticas e alcançáveis
- Responda sempre em português do Brasil
- Não faça julgamentos negativos sobre os hábitos do usuário"""


class Transaction(BaseModel):
    description: str
    amount: float
    category: Optional[str] = None
    date: Optional[str] = None
    type: Optional[str] = None  # "income" | "expense"


class ChatRequest(BaseModel):
    message: str
    transactions: Optional[list[Transaction]] = Field(default_factory=list)
    balance: Optional[float] = None
    currency: Optional[str] = "BRL"
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada no arquivo .env")
    yield
    conversation_sessions.clear()


app = FastAPI(
    title="Finance Chat API",
    description="Chatbot financeiro inteligente powered by Google Gemini",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_financial_context(
    transactions: list[Transaction],
    balance: Optional[float],
    currency: str,
) -> str:
    if not transactions and balance is None:
        return ""

    currency_symbol = {"BRL": "R$", "USD": "$", "EUR": "€"}.get(currency, currency)
    lines = ["\n--- DADOS FINANCEIROS DO USUÁRIO ---"]

    if balance is not None:
        lines.append(f"Saldo atual: {currency_symbol} {balance:,.2f}")

    if transactions:
        total_income = sum(t.amount for t in transactions if t.type == "income" or t.amount > 0)
        total_expenses = sum(abs(t.amount) for t in transactions if t.type == "expense" or t.amount < 0)

        lines.append(f"Total de receitas: {currency_symbol} {total_income:,.2f}")
        lines.append(f"Total de despesas: {currency_symbol} {total_expenses:,.2f}")

        categories: dict[str, float] = {}
        for t in transactions:
            if t.category:
                categories[t.category] = categories.get(t.category, 0) + abs(t.amount)

        if categories:
            lines.append("\nGastos por categoria:")
            for cat, total in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {cat}: {currency_symbol} {total:,.2f}")

        lines.append(f"\nÚltimas transações ({min(len(transactions), 10)} de {len(transactions)}):")
        for t in transactions[:10]:
            sign = "+" if (t.type == "income" or t.amount > 0) else "-"
            amount = abs(t.amount)
            date_str = f" ({t.date})" if t.date else ""
            cat_str = f" [{t.category}]" if t.category else ""
            lines.append(f"  {sign}{currency_symbol} {amount:,.2f} - {t.description}{cat_str}{date_str}")

    lines.append("--- FIM DOS DADOS ---\n")
    return "\n".join(lines)


def get_or_create_session(session_id: str) -> list[dict]:
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = []
    return conversation_sessions[session_id]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    history = get_or_create_session(request.session_id)

    financial_context = build_financial_context(
        request.transactions or [],
        request.balance,
        request.currency or "BRL",
    )

    user_content = request.message
    if financial_context:
        user_content = f"{financial_context}\nPergunta do usuário: {request.message}"

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )

        gemini_history = []
        for turn in history:
            gemini_history.append({"role": turn["role"], "parts": [turn["content"]]})

        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(user_content)
        assistant_reply = response.text

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao comunicar com Gemini: {str(exc)}")

    history.append({"role": "user", "content": request.message})
    history.append({"role": "model", "content": assistant_reply})

    # Keep at most 20 turns (40 messages) to avoid unbounded memory growth
    if len(history) > 40:
        conversation_sessions[request.session_id] = history[-40:]

    return ChatResponse(response=assistant_reply, session_id=request.session_id)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "finance-chat-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
