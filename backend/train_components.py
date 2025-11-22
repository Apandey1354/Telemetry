"""Quick script to train component models."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.component_modeling import train_component_models
from src.config import PROCESSED_DATA_DIR

if __name__ == "__main__":
    dataset_path = PROCESSED_DATA_DIR / "training_data_with_failures.parquet"
    print(f"Training component models with dataset: {dataset_path}")
    metrics = train_component_models(dataset_path)
    print("\nTraining complete!")
    print("Component model metrics:")
    for component, metric in metrics.items():
        print(f"  {component}: {metric}")

