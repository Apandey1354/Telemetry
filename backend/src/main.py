"""CLI entrypoint for Mechanical Karma backend."""

from __future__ import annotations

from pathlib import Path

import typer

from . import feature_engineering, karma_stream, modeling
from .config import PROCESSED_DATA_DIR

try:
    from . import component_modeling
except ImportError:
    component_modeling = None
from .firebase_push import push_scores
from .utils import configure_logging

app = typer.Typer(help="Mechanical Karma data pipeline CLI")
LOGGER = configure_logging("cli")


@app.command()
def ingest() -> None:
    """Build the per-lap dataset from raw CSVs."""

    feature_engineering.build_per_lap_dataset()


@app.command()
def train(
    dataset_path: Path = typer.Option(
        PROCESSED_DATA_DIR / "per_lap_features.parquet",
        exists=False,
        help="Optional path to a prepared per-lap dataset.",
    )
) -> None:
    """Train the configured karma model."""

    modeling.train(dataset_path)


@app.command("infer")
def run_inference(
    dataset_path: Path = typer.Option(
        PROCESSED_DATA_DIR / "per_lap_features.parquet",
        help="Dataset to score. Defaults to processed per-lap parquet.",
    ),
    output_path: Path = typer.Option(
        PROCESSED_DATA_DIR / "per_lap_with_karma.parquet",
        help="Where to write scored dataset.",
    ),
) -> None:
    """Run inference and save karma scores locally."""

    df = modeling.run_inference()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    LOGGER.info("Saved karma scores to %s", output_path)


@app.command("push-firebase")
def push_firebase(
    service_account: Path = typer.Option(
        None,
        help="Path to Firebase serviceAccountKey.json",
    ),
    db_url: str = typer.Option(
        None,
        help="Firebase Realtime Database URL",
    ),
    node: str = typer.Option("karma", help="Database node to update"),
) -> None:
    """Push the latest karma scores to Firebase."""

    push_scores(
        service_account=service_account,
        db_url=db_url,
        node=node,
    )


@app.command("karma-stream")
def karma_stream_cmd(
    dataset_path: Path = typer.Option(
        PROCESSED_DATA_DIR / "per_lap_features.parquet",
        help="Per-lap features parquet to stream from.",
    ),
    output_path: Path = typer.Option(
        PROCESSED_DATA_DIR / "karma_stream.parquet",
        help="Where to save component karma stream.",
    ),
    smoothing: float = typer.Option(
        0.6,
        min=0.0,
        max=0.99,
        help="EMA smoothing factor for karma scores.",
    ),
) -> None:
    """Simulate Mechanical Karma component scores per lap."""

    karma_stream.simulate_stream(
        dataset_path=dataset_path,
        smoothing=smoothing,
        output_path=output_path,
    )


@app.command("train-components")
def train_components(
    dataset_path: Path = typer.Option(
        PROCESSED_DATA_DIR / "training_data_with_failures.parquet",
        exists=False,
        help="Path to training dataset with component failure labels.",
    )
) -> None:
    """Train component-specific failure prediction models."""

    if component_modeling is None:
        LOGGER.error("Component modeling module not available")
        return
    
    component_modeling.train_component_models(dataset_path)


def main() -> None:
    app()


if __name__ == "__main__":
    main()




