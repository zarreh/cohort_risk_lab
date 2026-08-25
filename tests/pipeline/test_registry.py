from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from cohort.pipeline.registry import ModelMetadata, load_model_artifact, save_model_artifact


def test_round_trip_preserves_pipeline_and_metadata(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pipeline = Pipeline(steps=[("model", LogisticRegression())])
    metadata = ModelMetadata(
        version="v1_burden",
        label_name="Y_BURDEN",
        threshold=0.42,
        n_train=100,
        n_validation=25,
        metrics={"auroc": 0.81},
        feature_names=["AGE_AT_INDEX"],
    )

    version_dir = save_model_artifact(pipeline, metadata, tmp_path)
    loaded_pipeline, loaded_metadata = load_model_artifact(version_dir)

    assert isinstance(loaded_pipeline, Pipeline)
    assert loaded_metadata == metadata


def test_two_versions_coexist(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pipeline = Pipeline(steps=[("model", LogisticRegression())])
    meta_a = ModelMetadata("v1_burden", "Y_BURDEN", 0.4, 100, 25, {})
    meta_b = ModelMetadata("v1_cost", "Y_COST", 0.6, 100, 25, {})

    dir_a = save_model_artifact(pipeline, meta_a, tmp_path)
    dir_b = save_model_artifact(pipeline, meta_b, tmp_path)

    assert dir_a != dir_b
    assert (dir_a / "pipeline.joblib").exists()
    assert (dir_b / "pipeline.joblib").exists()
