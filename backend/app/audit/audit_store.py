"""Simple audit logging for optimisation results.

All optimisation calls are recorded with a unique ID, timestamp, input RFQ,
parsed payoff, scores and recommended alternative.  Records are persisted in
JSON format under the `demo_data` folder so that they survive server restarts.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import List, Optional

from ..models.rfq import AuditRecord, OptimizationResult, RFQInput, PayoffObject, QuoteAlternative


class AuditStore:
    """In‑memory and on‑disk storage for audit records."""

    def __init__(self, filepath: Optional[str] = None) -> None:
        # default location under demo_data
        if filepath is None:
            self.filepath = Path(__file__).resolve().parent / "../demo_data/audit_log.json"
        else:
            self.filepath = Path(filepath)
        self.filepath = self.filepath.resolve()
        self.records: List[AuditRecord] = []
        self._load()

    def _load(self) -> None:
        """Load existing records from disk if available."""
        if self.filepath.exists():
            try:
                data = json.loads(self.filepath.read_text())
                for item in data:
                    self.records.append(AuditRecord.parse_obj(item))
            except Exception:
                # ignore corrupt audit log
                self.records = []

    def _save(self) -> None:
        """Persist all records to disk."""
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with self.filepath.open("w", encoding="utf-8") as f:
                json.dump([r.dict() for r in self.records], f, indent=2, ensure_ascii=False)
        except Exception:
            # ignore save errors silently
            pass

    def log_record(self, result: OptimizationResult) -> None:
        """Create and store an audit record from an optimisation result.

        This method converts the optimisation result into an audit trail entry
        capturing the input RFQ, parsed payoff, parser notes, validation
        warnings, original scores, alternatives and the recommendation.  It
        includes version identifiers for scoring and synthetic data to aid
        reproducibility across releases.
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        # Extract parser notes and validation warnings from current_quote_quality if present
        parser_notes = result.current_quote_quality.get("parser_notes", {}) if isinstance(result.current_quote_quality, dict) else {}
        validation_warnings = result.missing_fields
        # Compose original scores dictionary: win probability detail, desk econ and risk assessment
        original_scores = {
            "win_probability_detail": result.current_quote_quality.get("win_probability_detail"),
            "desk_economics_score": result.current_quote_quality.get("desk_economics_score"),
            "risk_assessment": result.current_quote_quality.get("risk_assessment"),
        }
        record = AuditRecord(
            audit_id=result.audit_id,
            timestamp=timestamp,
            input_rfq=RFQInput(
                raw_text=result.original_payoff.dict().get("raw_text", "") if hasattr(result.original_payoff, "raw_text") else "",
                client_segment=result.original_payoff.client_segment,
                region=result.original_payoff.region,
            ),
            parsed_payoff=result.original_payoff,
            parser_notes=parser_notes,
            validation_warnings=validation_warnings,
            original_scores=original_scores,
            alternatives=result.alternatives,
            recommendation=result.recommended_alternative_id,
            ranking_version="0.2",  # increment when scoring formula changes
            synthetic_data_version="0.2",  # increment when synthetic profiles change
            limitations=result.limitations,
        )
        self.records.append(record)
        self._save()

    def get_records(self) -> List[AuditRecord]:
        """Return all audit records."""
        return self.records
