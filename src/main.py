"""
FastAPI entrypoint exposing the allowance anomaly detection agent.

Run with:
    python -m src.main
"""
import logging
import sys
from pathlib import Path

# Ensure the project root is importable as "src...", regardless of how this
# file is invoked (e.g. `python src/main.py`, `python -m src.main`, or via
# uvicorn's --reload subprocess).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gradio as gr
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from src.agents.anamoly_agent import run_anomaly_check
from src.agents.financerecon_agent import run_financerecon_check
from src.ui.chatbotui import demo as chatbot_ui

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Vendor Agreement Anomaly Detection API")
app = gr.mount_gradio_app(app, chatbot_ui, path="/chat")


class AnomalyCheckRequest(BaseModel):
    agreement_id: int


class AnomalyCheckResponse(BaseModel):
    agreement_id: int
    result: str


class FinanceReconRequest(BaseModel):
    agreement_id: int


class FinanceReconResponse(BaseModel):
    agreement_id: int
    result: str


@app.post("/anomaly-check", response_model=AnomalyCheckResponse)
def anomaly_check(request: AnomalyCheckRequest) -> AnomalyCheckResponse:
    """Run the allowance anomaly detection agent for the given agreement id."""
    logger.info("Running anomaly check for agreement %s", request.agreement_id)
    result = run_anomaly_check(request.agreement_id)
    return AnomalyCheckResponse(agreement_id=request.agreement_id, result=result)


@app.post("/finance-recon", response_model=FinanceReconResponse)
def finance_recon(request: FinanceReconRequest) -> FinanceReconResponse:
    """Run the finance reconciliation agent for the given agreement id."""
    logger.info("Running finance reconciliation for agreement %s", request.agreement_id)
    result = run_financerecon_check(request.agreement_id)
    return FinanceReconResponse(agreement_id=request.agreement_id, result=result)


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
