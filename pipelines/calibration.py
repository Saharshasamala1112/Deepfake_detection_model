from __future__ import annotations

import logging
from typing import Dict, Any, Optional

import numpy as np

try:
    # If the project provides a central calibration implementation, prefer it.
    # Import is optional: fall back to local implementation when missing.
    from system.calibration import calibrate as external_calibrate  # type: ignore
except Exception:
    external_calibrate = None

LOG = logging.getLogger(__name__)


def _sigmoid_calibrate(score: float, scale: float = 5.0, shift: float = 0.5) -> float:
    """Sigmoid-based calibration mapping a score in [0,1] to a calibrated confidence.

    Args:
        score: input score (expected 0..1, will be clipped)
        scale: controls steepness of the sigmoid
        shift: midpoint of sigmoid

    Returns:
        Calibrated score in (0,1)
    """
    s = float(score)
    # Clip to reasonable numeric range to avoid overflow
    s = max(0.0, min(1.0, s))
    return float(1.0 / (1.0 + np.exp(-scale * (s - shift))))


def apply_calibration(
    result: Dict[str, Any],
    method: str = "sigmoid",
    *,
    scale: float = 5.0,
    shift: float = 0.5,
    use_external_when_available: bool = True,
) -> Dict[str, Any]:
    """Compute and attach a calibrated `confidence` to a result dict.

    The function will look for `final_score`, then fall back to `confidence`,
    then `raw_score`. If none are present it will assume 0.0.

    Args:
        result: input/result dictionary produced by pipelines.
        method: calibration method name: 'sigmoid' or 'external'.
        scale, shift: parameters for sigmoid calibration.
        use_external_when_available: when method=='external', allow fallback to local

    Returns:
        A shallow copy of `result` with `confidence` set to the calibrated value.
    """
    if not isinstance(result, dict):
        raise TypeError("result must be a dict")

    # Determine base score
    score = None
    for k in ("final_score", "confidence", "raw_score"):
        if k in result:
            try:
                score = float(result[k])
                break
            except Exception:
                continue
    if score is None:
        score = 0.0

    calibrated = 0.0
    if method == "external" and external_calibrate is not None and use_external_when_available:
        try:
            calibrated = float(external_calibrate(score))
        except Exception:
            LOG.exception("external_calibrate failed; falling back to sigmoid")
            calibrated = _sigmoid_calibrate(score, scale=scale, shift=shift)
    else:
        # default: sigmoid-based
        calibrated = _sigmoid_calibrate(score, scale=scale, shift=shift)

    # safety clip
    calibrated = float(max(0.0, min(1.0, calibrated)))

    out = dict(result)
    out["confidence"] = calibrated
    return out


__all__ = ["apply_calibration", "_sigmoid_calibrate"]
