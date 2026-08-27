"""ML Inference & Explainability Endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional

from app.ml.predictor import ml_predictor

router = APIRouter()


class MLPredictRequest(BaseModel):
    phq9_responses: Dict[str, int]   # item_number (1-9) -> score (0-3)
    gad7_responses: Dict[str, int]   # item_number (1-7) -> score (0-3)
    pss10_responses: Dict[str, int]  # item_number (1-10) -> score (0-4)


class MLPredictResponse(BaseModel):
    risk_label: str
    confidence: float
    top_feature_importance: Dict[str, float]
    shap_features: Dict[str, float]       # alias so both field names work
    model_name: str = "Random Forest (Clinical Screening)"


@router.post("/predict", response_model=MLPredictResponse)
async def predict_risk(data: MLPredictRequest):
    """Run direct ML inference on 26 questionnaire answers."""
    all_responses = {
        "phq9":  {int(k): v for k, v in data.phq9_responses.items()},
        "gad7":  {int(k): v for k, v in data.gad7_responses.items()},
        "pss10": {int(k): v for k, v in data.pss10_responses.items()},
    }
    label, conf, shap_feats = ml_predictor.predict(all_responses)
    return MLPredictResponse(
        risk_label=label,
        confidence=conf,
        top_feature_importance=shap_feats,
        shap_features=shap_feats,
    )
