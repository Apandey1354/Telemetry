# What to Do After Training the Model

## Step 1: Verify Training Completed ✅

Check if the model was trained successfully:

```bash
cd backend
python -c "import json; from pathlib import Path; p = Path('artifacts/training_metrics.json'); print(json.dumps(json.loads(p.read_text()), indent=2) if p.exists() else 'Not found')"
```

You should see files in `backend/artifacts/`:
- `karma_model.pkl` - The trained model
- `feature_scaler.pkl` - Feature scaler (if scaling enabled)
- `training_metrics.json` - Training performance metrics
- `feature_meta.json` - List of features used

## Step 2: Review Training Metrics 📊

Check the training performance:

```bash
# View metrics
cat backend/artifacts/training_metrics.json
```

Look for:
- **ROC AUC**: Should be > 0.7 (higher is better, max 1.0)
- **Precision**: How many predicted failures were actual failures
- **Recall**: How many actual failures were caught
- **F1 Score**: Balance of precision and recall
- **Accuracy**: Overall correctness

**Good metrics example:**
```json
{
  "roc_auc": 0.85,
  "precision_dnf": 0.78,
  "recall_dnf": 0.82,
  "f1_dnf": 0.80,
  "accuracy": 0.88
}
```

## Step 3: Run Inference on Your Data 🔮

Use the trained model to predict failures on new data:

```bash
# Process your telemetry data first (if not already done)
python -m src.main ingest

# Run inference to get karma scores
python -m src.main infer
```

This will:
- Load your processed telemetry data
- Generate karma scores (0-100) for each lap
- Save results to `data/processed/per_lap_with_karma.parquet`

## Step 4: Generate Component-Level Karma Scores ⚙️

Create per-component karma scores for visualization:

```bash
python -m src.main karma-stream
```

This creates `data/processed/karma_stream.parquet` with:
- Engine karma
- Gearbox karma
- Brakes karma
- Tires karma

## Step 5: Use in React Dashboard 🎨

The trained model is automatically used when you:

1. **Start the backend API:**
   ```bash
   cd backend
   python api.py
   ```

2. **Start the React frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Upload telemetry data** through the web interface

The dashboard will:
- Use the trained model to predict DNF probability
- Show component-level karma scores
- Display real-time risk visualization

## Step 6: Evaluate Model Performance 📈

### Check Predictions vs Reality

If you have labeled test data:

```python
import pandas as pd
from src.modeling import run_inference, load_artifacts

# Load predictions
predictions = run_inference()
actual = pd.read_parquet("data/processed/training_data_with_failures.parquet")

# Compare predictions with actual failures
# (You can create a custom evaluation script)
```

### Feature Importance (Random Forest)

If using Random Forest, check which features matter most:

```python
from joblib import load
import pandas as pd

model = load("backend/artifacts/karma_model.pkl")
feature_names = json.loads(Path("backend/artifacts/feature_meta.json").read_text())["feature_names"]

# Get feature importances
importances = pd.DataFrame({
    "feature": feature_names,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print(importances.head(10))
```

## Step 7: Improve the Model (Optional) 🔧

If metrics are low, try:

### 1. More Training Data
```bash
# Generate more synthetic data
python generate_training_data.py
# Edit the script to increase num_vehicles
```

### 2. Different Model
Edit `backend/src/config.py`:
```python
# Change model type
MODEL_TYPE=mlp  # or random_forest
```

### 3. Hyperparameter Tuning
Edit `backend/src/modeling.py` to adjust:
- `n_estimators` (Random Forest)
- `max_depth` (Random Forest)
- `hidden_layer_sizes` (MLP)
- `learning_rate` (MLP)

### 4. Feature Engineering
Add more features in `backend/src/config.py`:
```python
TELEMETRY_AGGREGATIONS = (
    # Add more aggregations
    AggregationSpec("new_signal", stats=("mean", "max", "std")),
)
```

## Step 8: Deploy to Production 🚀

### Option A: Keep Using React Dashboard
- The current setup is ready for production
- Just deploy backend API and frontend

### Option B: Push to Firebase
```bash
python -m src.main push-firebase \
  --service-account ../secrets/serviceAccountKey.json \
  --db-url https://your-project.firebaseio.com
```

### Option C: Create API Endpoints
The Flask API (`backend/api.py`) already has endpoints for:
- `/api/upload` - Upload telemetry
- `/api/vehicle/<id>` - Get vehicle data
- `/api/karma/<id>` - Get karma scores

## Troubleshooting ❗

### Model Not Found Error
```bash
# Make sure you trained the model
python -m src.main train --dataset-path data/processed/training_data_with_failures.parquet
```

### Low Accuracy
- Check if training data is balanced
- Try different model types
- Add more features
- Increase training data size

### Inference Errors
- Ensure processed data has same features as training data
- Check feature names match
- Verify scaler was saved during training

## Quick Reference Commands 📝

```bash
# Train model
python -m src.main train --dataset-path data/processed/training_data_with_failures.parquet

# Run inference
python -m src.main infer

# Generate karma stream
python -m src.main karma-stream

# Start API
python api.py

# Start React app
cd frontend && npm run dev
```

## Next Steps 🎯

1. ✅ Train the model (you're here!)
2. ✅ Verify training metrics
3. ✅ Run inference on your data
4. ✅ Visualize in React dashboard
5. ✅ Monitor performance
6. ✅ Iterate and improve

Your model is now ready to predict mechanical failures! 🎉






