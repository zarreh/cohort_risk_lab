from cohort.pipeline.cards.model_card import generate_model_card
from cohort.pipeline.registry import ModelMetadata


def test_model_card_includes_label_and_metrics() -> None:
    metadata = ModelMetadata(
        version="v1_burden",
        label_name="Y_BURDEN",
        threshold=0.42,
        n_train=1000,
        n_validation=250,
        metrics={"auroc": 0.812345},
        feature_names=["AGE_AT_INDEX", "HAS_DIABETES"],
    )
    card = generate_model_card(metadata)
    assert "Y_BURDEN" in card
    assert "0.4200" in card
    assert "0.8123" in card
    assert "AGE_AT_INDEX" in card
    assert "RACE and ETHNICITY are deliberately excluded" in card


def test_unknown_label_falls_back_to_raw_name() -> None:
    metadata = ModelMetadata("v_x", "Y_MYSTERY", 0.5, 1, 1, {})
    card = generate_model_card(metadata)
    assert "Y_MYSTERY" in card
