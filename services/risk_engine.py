"""Feedback-driven risk assessment engine for incident triage."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


RISK_ORDER = ["low", "medium", "high", "critical"]
RISK_TO_SCORE = {level: index for index, level in enumerate(RISK_ORDER)}
SCORE_TO_RISK = {index: level for level, index in RISK_TO_SCORE.items()}

ISSUE_PROFILES: Dict[str, Dict[str, str]] = {
    "chemical spill": {
        "category": "private issue",
        "risk_level": "critical",
        "responder_type": "emergency",
        "health_concern": "Possible toxic exposure for nearby people.",
        "ecosystem_impact": "Can contaminate land and water and harm wildlife.",
        "summary": "A possible chemical spill has been detected and needs immediate containment.",
        "action": "Keep people away, isolate the area, and notify emergency responders.",
    },
    "fire hazard": {
        "category": "private issue",
        "risk_level": "high",
        "responder_type": "police_fire_medical",
        "health_concern": "Smoke, heat, and flames can quickly endanger nearby people.",
        "ecosystem_impact": "Can spread rapidly and damage habitats and air quality.",
        "summary": "A fire-related hazard has been detected near the reported location.",
        "action": "Move to safety and alert emergency services if the risk is active.",
    },
    "pothole": {
        "category": "public issue",
        "risk_level": "low",
        "responder_type": "municipal",
        "health_concern": "Main risk is traffic accidents and vehicle damage.",
        "ecosystem_impact": "Minimal ecosystem impact.",
        "summary": "A roadway damage issue has been detected and likely needs municipal repair.",
        "action": "Route to municipal maintenance and monitor if the road becomes dangerous.",
    },
    "plastic waste near water": {
        "category": "environmental issue",
        "risk_level": "high",
        "responder_type": "environmental",
        "health_concern": "Can indirectly affect people through contamination and poor sanitation.",
        "ecosystem_impact": "Can spread pollution through waterways and harm aquatic life.",
        "summary": "Pollution near water has been detected and may spread quickly downstream.",
        "action": "Route to an environmental cleanup team and inspect nearby water flow.",
    },
    "trash dumping": {
        "category": "household issue",
        "risk_level": "medium",
        "responder_type": "environmental",
        "health_concern": "Can attract pests and create sanitation issues over time.",
        "ecosystem_impact": "Can degrade soil quality and nearby habitats.",
        "summary": "Illegal or unsafe dumping has been detected in the reported area.",
        "action": "Schedule cleanup, inspect for repeat dumping, and advise the reporter to keep distance.",
    },
    "environmental hazard": {
        "category": "environmental issue",
        "risk_level": "medium",
        "responder_type": "environmental",
        "health_concern": "Potential health concern depending on exposure and proximity.",
        "ecosystem_impact": "May negatively affect the surrounding environment.",
        "summary": "An environmental hazard has been detected and should be reviewed.",
        "action": "Inspect the location and route to the most relevant department.",
    },
}

KEYWORD_SCORE_BUMPS = {
    "fire": 2,
    "smoke": 1,
    "flames": 2,
    "explosion": 3,
    "chemical": 2,
    "toxic": 2,
    "spill": 2,
    "gas": 2,
    "leak": 1,
    "collapsed": 2,
    "flood": 2,
    "river": 1,
    "water": 1,
    "trash": 1,
    "garbage": 1,
    "oil": 2,
    "911": 3,
    "evacuate": 3,
    "injured": 2,
    "bleeding": 3,
}

RESPONDER_HINTS = {
    "environmental": ["river", "water", "pollution", "plastic", "trash", "garbage", "wildlife"],
    "municipal": ["road", "pothole", "street", "sidewalk", "traffic"],
    "police_fire_medical": ["fire", "smoke", "hazard", "injured", "medical"],
    "emergency": ["explosion", "toxic", "911", "evacuate", "bleeding", "collapsed"],
}

EMERGENCY_TERMS = {"911", "evacuate", "explosion", "bleeding", "toxic", "gas leak"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clamp_score(score: int) -> int:
    return max(0, min(score, len(RISK_ORDER) - 1))


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


class RiskEngine:
    """Derives structured risk predictions and improves with verified outcomes."""

    def __init__(self, data_dir: Path, model_version: str = "risk-engine-v1") -> None:
        self.data_dir = data_dir
        self.model_version = model_version
        self.predictions_path = self.data_dir / "risk_predictions.json"
        self.feedback_path = self.data_dir / "risk_feedback.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_file(self.predictions_path)
        self._ensure_file(self.feedback_path)

    def _ensure_file(self, path: Path) -> None:
        if not path.exists():
            path.write_text("[]", encoding="utf-8")

    def _load_records(self, path: Path) -> List[Dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def _save_records(self, path: Path, records: List[Dict[str, Any]]) -> None:
        path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def _find_keywords(self, text: str) -> List[str]:
        lowered = text.lower()
        return [term for term in KEYWORD_SCORE_BUMPS if term in lowered]

    def _get_profile(self, issue_type: str) -> Dict[str, str]:
        return deepcopy(ISSUE_PROFILES.get(issue_type, ISSUE_PROFILES["environmental hazard"]))

    def _learning_snapshot(self, issue_type: str) -> Dict[str, Any]:
        feedback_records = self._load_records(self.feedback_path)
        issue_records = [record for record in feedback_records if record.get("issue_type") == issue_type]
        risk_counter = Counter(record.get("final_risk_level") for record in issue_records if record.get("final_risk_level"))
        responder_counter = Counter(
            record.get("final_responder_type") for record in issue_records if record.get("final_responder_type")
        )
        category_counter = Counter(record.get("final_category") for record in issue_records if record.get("final_category"))

        dominant_risk_level, dominant_risk_count = risk_counter.most_common(1)[0] if risk_counter else ("", 0)
        dominant_responder, dominant_responder_count = (
            responder_counter.most_common(1)[0] if responder_counter else ("", 0)
        )
        dominant_category, dominant_category_count = category_counter.most_common(1)[0] if category_counter else ("", 0)

        return {
            "feedback_count": len(issue_records),
            "dominant_risk_level": dominant_risk_level,
            "dominant_risk_ratio": round(_safe_ratio(dominant_risk_count, len(issue_records)), 3),
            "dominant_responder_type": dominant_responder,
            "dominant_responder_ratio": round(_safe_ratio(dominant_responder_count, len(issue_records)), 3),
            "dominant_category": dominant_category,
            "dominant_category_ratio": round(_safe_ratio(dominant_category_count, len(issue_records)), 3),
        }

    def assess_incident(
        self,
        *,
        issue_type: str,
        category: str,
        latitude: str = "",
        longitude: str = "",
        address: str = "",
        reporter_text: str = "",
        reporter_transcript: str = "",
        image_filename: str = "",
        llm_suggested_risk: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a structured risk assessment from rules, priors, and optional LLM hints."""
        profile = self._get_profile(issue_type)
        combined_text = " ".join(
            value.strip()
            for value in [issue_type, category, address, reporter_text, reporter_transcript, image_filename]
            if value
        ).lower()
        matched_keywords = self._find_keywords(combined_text)
        learning_snapshot = self._learning_snapshot(issue_type)

        risk_score = RISK_TO_SCORE[profile["risk_level"]]
        predicted_category = category or profile["category"]
        predicted_responder = profile["responder_type"]
        prediction_sources = ["rules"]
        reason_codes = [f"issue_type:{issue_type}"]

        for keyword in matched_keywords:
            risk_score = _clamp_score(risk_score + KEYWORD_SCORE_BUMPS[keyword])
            reason_codes.append(f"keyword:{keyword}")

        for responder_type, responder_keywords in RESPONDER_HINTS.items():
            if any(keyword in combined_text for keyword in responder_keywords):
                predicted_responder = responder_type
                reason_codes.append(f"responder_hint:{responder_type}")
                break

        if any(term in combined_text for term in EMERGENCY_TERMS):
            risk_score = max(risk_score, RISK_TO_SCORE["critical"])
            predicted_responder = "emergency"
            reason_codes.append("emergency_terms_detected")

        if llm_suggested_risk in RISK_TO_SCORE:
            risk_score = max(risk_score, RISK_TO_SCORE[llm_suggested_risk])
            prediction_sources.append("llm_hint")
            reason_codes.append(f"llm_hint:{llm_suggested_risk}")

        if learning_snapshot["feedback_count"] >= 3:
            prediction_sources.append("feedback")
            reason_codes.append(f"feedback_support:{learning_snapshot['feedback_count']}")

            if learning_snapshot["dominant_risk_level"] and learning_snapshot["dominant_risk_ratio"] >= 0.6:
                risk_score = max(risk_score, RISK_TO_SCORE[learning_snapshot["dominant_risk_level"]])
            if learning_snapshot["dominant_category"] and learning_snapshot["dominant_category_ratio"] >= 0.6:
                predicted_category = learning_snapshot["dominant_category"]
            if (
                learning_snapshot["dominant_responder_type"]
                and learning_snapshot["dominant_responder_ratio"] >= 0.6
            ):
                predicted_responder = learning_snapshot["dominant_responder_type"]

        predicted_risk_level = SCORE_TO_RISK[_clamp_score(risk_score)]
        if predicted_risk_level == "critical":
            predicted_responder = "emergency"

        confidence = 0.55
        confidence += min(len(matched_keywords), 3) * 0.05
        confidence += min(learning_snapshot["feedback_count"], 5) * 0.04
        if llm_suggested_risk == predicted_risk_level:
            confidence += 0.05
        if latitude and longitude:
            confidence += 0.03
        if reporter_text or reporter_transcript:
            confidence += 0.04
        confidence = round(max(0.35, min(confidence, 0.95)), 3)

        requires_human_review = predicted_risk_level in {"high", "critical"} or confidence < 0.7
        feature_snapshot = {
            "issue_type": issue_type,
            "initial_category": category,
            "latitude": latitude,
            "longitude": longitude,
            "address": address,
            "reporter_text_present": bool(reporter_text.strip()),
            "reporter_transcript_present": bool(reporter_transcript.strip()),
            "image_filename": image_filename,
            "matched_keywords": matched_keywords,
        }

        return {
            "model_version": self.model_version,
            "predicted_category": predicted_category,
            "predicted_risk_level": predicted_risk_level,
            "predicted_responder_type": predicted_responder,
            "confidence": confidence,
            "requires_human_review": requires_human_review,
            "prediction_sources": prediction_sources,
            "reason_codes": reason_codes,
            "learning_snapshot": learning_snapshot,
            "feature_snapshot": feature_snapshot,
            "baseline_profile": {
                "health_concern": profile["health_concern"],
                "ecosystem_impact": profile["ecosystem_impact"],
                "summary": profile["summary"],
                "action": profile["action"],
            },
        }

    def record_prediction(self, ticket_id: str, issue_type: str, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a prediction event so it can later be paired with verified feedback."""
        record = {
            "ticket_id": ticket_id,
            "issue_type": issue_type,
            "predicted_category": assessment["predicted_category"],
            "predicted_risk_level": assessment["predicted_risk_level"],
            "predicted_responder_type": assessment["predicted_responder_type"],
            "confidence": assessment["confidence"],
            "requires_human_review": assessment["requires_human_review"],
            "prediction_sources": assessment["prediction_sources"],
            "reason_codes": assessment["reason_codes"],
            "learning_snapshot": assessment["learning_snapshot"],
            "feature_snapshot": assessment["feature_snapshot"],
            "model_version": assessment["model_version"],
            "created_at": _now_iso(),
        }
        prediction_records = self._load_records(self.predictions_path)
        prediction_records.append(record)
        self._save_records(self.predictions_path, prediction_records)
        return record

    def record_feedback(
        self,
        ticket: Dict[str, Any],
        feedback: Dict[str, Any],
        reviewer_department_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store a verified incident outcome for future learning."""
        assessment = ticket.get("risk_assessment", {})
        predicted_category = assessment.get("predicted_category", ticket.get("category", ""))
        predicted_risk_level = assessment.get("predicted_risk_level", ticket.get("risk_level", ""))
        predicted_responder_type = assessment.get(
            "predicted_responder_type", ticket.get("assigned_responder_type", "")
        )

        was_prediction_correct = feedback.get("was_prediction_correct")
        if was_prediction_correct is None:
            was_prediction_correct = (
                predicted_category == feedback.get("final_category")
                and predicted_risk_level == feedback.get("final_risk_level")
                and predicted_responder_type == feedback.get("final_responder_type")
            )

        record = {
            "ticket_id": ticket["ticket_id"],
            "issue_type": ticket.get("issue_type", "environmental hazard"),
            "predicted_category": predicted_category,
            "predicted_risk_level": predicted_risk_level,
            "predicted_responder_type": predicted_responder_type,
            "final_category": feedback["final_category"],
            "final_risk_level": feedback["final_risk_level"],
            "final_responder_type": feedback["final_responder_type"],
            "final_status": feedback.get("final_status", "resolved"),
            "emergency_escalated": feedback.get("emergency_escalated", False),
            "responder_notes": feedback.get("responder_notes", ""),
            "was_prediction_correct": was_prediction_correct,
            "reviewer_department_id": reviewer_department_id,
            "feature_snapshot": assessment.get("feature_snapshot", {}),
            "model_version": assessment.get("model_version", self.model_version),
            "created_at": _now_iso(),
        }
        feedback_records = self._load_records(self.feedback_path)
        feedback_records.append(record)
        self._save_records(self.feedback_path, feedback_records)
        return record

    def get_training_summary(self) -> Dict[str, Any]:
        """Summarize the feedback history driving local learning."""
        feedback_records = self._load_records(self.feedback_path)
        risk_distribution = Counter()
        responder_distribution = Counter()
        category_distribution = Counter()
        issue_type_stats: Dict[str, Dict[str, int]] = {}
        correct_predictions = 0

        for record in feedback_records:
            issue_type = record.get("issue_type", "unknown")
            issue_stats = issue_type_stats.setdefault(
                issue_type,
                {
                    "feedback_count": 0,
                    "correct_predictions": 0,
                    "critical_outcomes": 0,
                },
            )
            issue_stats["feedback_count"] += 1
            if record.get("was_prediction_correct"):
                issue_stats["correct_predictions"] += 1
                correct_predictions += 1
            if record.get("final_risk_level") == "critical":
                issue_stats["critical_outcomes"] += 1

            if record.get("final_risk_level"):
                risk_distribution[record["final_risk_level"]] += 1
            if record.get("final_responder_type"):
                responder_distribution[record["final_responder_type"]] += 1
            if record.get("final_category"):
                category_distribution[record["final_category"]] += 1

        total_feedback = len(feedback_records)
        average_prediction_accuracy = round(_safe_ratio(correct_predictions, total_feedback), 3)

        return {
            "model_version": self.model_version,
            "total_feedback_records": total_feedback,
            "issue_type_stats": issue_type_stats,
            "risk_distribution": dict(risk_distribution),
            "responder_distribution": dict(responder_distribution),
            "category_distribution": dict(category_distribution),
            "average_prediction_accuracy": average_prediction_accuracy,
        }


risk_engine = RiskEngine(Path(__file__).resolve().parent.parent / "data")
