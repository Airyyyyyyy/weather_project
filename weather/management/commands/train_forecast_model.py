"""Train the real weather forecast models (tomorrow's temperature + rain
likelihood) on the historical dataset built by build_training_dataset.

Usage: python manage.py train_forecast_model
"""
import json
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, mean_absolute_error, precision_score,
    recall_score, roc_auc_score, root_mean_squared_error,
)

from weather.ml.cities import CITIES
from weather.ml.dataset import FEATURE_COLUMNS, build_feature_row

DATA_PATH = settings.BASE_DIR / "weather" / "ml" / "data" / "historical_weather.csv"
ARTIFACTS_DIR = settings.BASE_DIR / "weather" / "ml" / "artifacts"

TEST_CUTOFF = pd.Timestamp("2023-01-01")  # last year of data held out as the test set


class Command(BaseCommand):
    help = "Train the temperature regressor and rain classifier on the historical dataset"

    def handle(self, *args, **options):
        if not DATA_PATH.exists():
            raise CommandError(
                f"{DATA_PATH} not found. Run `python manage.py build_training_dataset` first."
            )

        df = pd.read_csv(DATA_PATH, parse_dates=["date"])
        lat_by_city = {c["name"]: c["lat"] for c in CITIES}
        lon_by_city = {c["name"]: c["lon"] for c in CITIES}

        features = []
        for row in df.itertuples(index=False):
            feature_row = build_feature_row(
                lat=lat_by_city[row.city],
                lon=lon_by_city[row.city],
                temp_c=row.temp_c,
                humidity_pct=row.humidity_pct,
                pressure_hpa=row.pressure_hpa,
                wind_speed_ms=row.wind_speed_ms,
                condition_flags={
                    "is_rainy": row.is_rainy, "is_snowy": row.is_snowy,
                    "is_cloudy": row.is_cloudy, "is_clear": row.is_clear,
                },
                date=row.date.date(),
            )
            features.append(feature_row)

        X = pd.DataFrame(features, columns=FEATURE_COLUMNS)
        y_temp = df["y_temp_next"]
        y_rain = df["y_rain_next"]

        # Time-based split; drop the one boundary day per city whose target
        # crosses the cutoff, so no test-period information leaks into training.
        boundary_day = TEST_CUTOFF - pd.Timedelta(days=1)
        train_mask = df["date"] < boundary_day
        test_mask = df["date"] >= TEST_CUTOFF

        X_train, X_test = X[train_mask], X[test_mask]
        y_temp_train, y_temp_test = y_temp[train_mask], y_temp[test_mask]
        y_rain_train, y_rain_test = y_rain[train_mask], y_rain[test_mask]

        self.stdout.write(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")

        self.stdout.write("Training temperature regressor...")
        temp_regressor = RandomForestRegressor(
            n_estimators=100, min_samples_leaf=20, random_state=42, n_jobs=-1
        )
        temp_regressor.fit(X_train, y_temp_train)
        temp_pred = temp_regressor.predict(X_test)

        mae = mean_absolute_error(y_temp_test, temp_pred)
        rmse = root_mean_squared_error(y_temp_test, temp_pred)
        baseline_mae = mean_absolute_error(y_temp_test, X_test["temp_c"])  # naive "tomorrow = today"

        self.stdout.write("Training rain classifier...")
        rain_classifier = RandomForestClassifier(
            n_estimators=100, min_samples_leaf=30, random_state=42, n_jobs=-1,
            class_weight="balanced",
        )
        rain_classifier.fit(X_train, y_rain_train)
        rain_pred = rain_classifier.predict(X_test)
        rain_proba = rain_classifier.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_rain_test, rain_pred)
        precision = precision_score(y_rain_test, rain_pred, zero_division=0)
        recall = recall_score(y_rain_test, rain_pred, zero_division=0)
        auc = roc_auc_score(y_rain_test, rain_proba)

        metrics = {
            "trained_at": datetime.utcnow().isoformat() + "Z",
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "test_period": f"{TEST_CUTOFF.date()} onward",
            "temperature_regression": {
                "mae_celsius": round(float(mae), 3),
                "rmse_celsius": round(float(rmse), 3),
                "naive_persistence_baseline_mae_celsius": round(float(baseline_mae), 3),
            },
            "rain_classification": {
                "accuracy": round(float(accuracy), 3),
                "precision": round(float(precision), 3),
                "recall": round(float(recall), 3),
                "roc_auc": round(float(auc), 3),
                "positive_rate_test_set": round(float(np.mean(y_rain_test)), 3),
            },
        }

        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(temp_regressor, ARTIFACTS_DIR / "temp_regressor.joblib", compress=3)
        joblib.dump(rain_classifier, ARTIFACTS_DIR / "rain_classifier.joblib", compress=3)
        (ARTIFACTS_DIR / "feature_columns.json").write_text(json.dumps(FEATURE_COLUMNS, indent=2))
        (ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

        self.stdout.write(self.style.SUCCESS(f"Saved model artifacts to {ARTIFACTS_DIR}"))
        self.stdout.write(json.dumps(metrics, indent=2))
