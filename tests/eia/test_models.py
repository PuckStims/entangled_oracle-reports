import pytest

from eia_engine.models import EIARegisterBlock, EIASourceEvidence


def test_register_block_validates_register_name():
    with pytest.raises(ValueError, match="Unknown EIA register"):
        EIARegisterBlock(
            register="unknown",
            dominant_mode="Direct Spark",
            secondary_mode=None,
            score=0.7,
            mechanism="Movement begins.",
            distortion="Urgency Collapse",
            restoration="Return later.",
            experiment="Observe.",
        )


def test_source_evidence_validates_score_range():
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        EIASourceEvidence("natal_astrology", "signal", 1.4)
