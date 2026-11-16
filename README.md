# Weather Dashboard

A Django weather app that tracks multiple cities via OpenWeatherMap's current-conditions
API, and predicts each city's next day (temperature + rain likelihood) with a
machine learning model trained on real historical weather data — not synthetic
data, and not an LLM wrapper. A separate keyword-based "Quick Help" widget
answers simple questions about tracked cities; it's plain `if/else` logic and
is not presented as AI.

<!-- screenshot: dashboard with a few tracked cities -->
<!-- screenshot: quick help widget open -->

## Architecture

```
weather/
  views.py                 thin request/response handlers only
  services/
    weather_api.py         OpenWeatherMap client (timeouts, error handling)
    recommendations.py     rule-based clothing/activity tips + alerts
    chat.py                Quick Help keyword-matching logic
  ml/
    cities.py               training-set city list (name, country, lat/lon)
    dataset.py               shared feature engineering (train + inference call the same code)
    forecast_model.py       loads trained models, exposes predict()
    data/historical_weather.csv   committed training dataset
    artifacts/               trained models + metrics.json
  management/commands/
    build_training_dataset.py   fetch real historical data from Open-Meteo
    train_forecast_model.py     train + evaluate the forecast models
```

Tracked cities live in the Django session — there's no user database. That's
a deliberate scope choice for a no-login demo, not an oversight (see
Limitations below).

## ML methodology

**Data**: [Open-Meteo's historical weather archive](https://open-meteo.com/en/docs/historical-weather-api)
(ERA5 reanalysis, no API key required), daily records for 38 cities chosen
for geographic/climatic diversity, 2019-01-01 through 2023-12-31
(~65,700 rows, `weather/ml/data/historical_weather.csv`).

**Design constraint**: at inference time, the app only has what one live
OpenWeatherMap "current weather" call returns (temperature, humidity,
pressure, wind speed, text description, lat/lon). Every training feature is
built to be derivable from that same set, and both training and inference
call the exact same feature-engineering functions in `weather/ml/dataset.py`
— this is what prevents the model from being trained on information it will
never have when actually serving a prediction.

**Features** (13): latitude, longitude, today's temperature/humidity/pressure/
wind speed, four 0/1 condition flags (rainy/snowy/cloudy/clear — derived from
WMO weather codes during training, from OpenWeatherMap's text description
during inference, via one shared mapping), and cyclical (sin/cos) encodings
of month and day-of-year.

**Targets**: tomorrow's mean temperature (regression) and whether tomorrow
sees measurable precipitation, ≥1mm (binary classification).

**Split**: time-based, not random — trained on 2019–2022, evaluated only on
2023 (held out entirely), with the one boundary day per city that would leak
across the cutoff excluded from training.

**Models**: `RandomForestRegressor` (temperature) and `RandomForestClassifier`
with `class_weight='balanced'` (rain), both `n_estimators=300`, scikit-learn.

**Results** (held-out 2023 test set, see `weather/ml/artifacts/metrics.json`):

| Metric | Value |
|---|---|
| Temperature MAE | 1.28°C (vs. 1.35°C for a naive "tomorrow = today" baseline) |
| Temperature RMSE | 1.80°C |
| Rain accuracy | 77.9% |
| Rain precision / recall | 0.70 / 0.56 |
| Rain ROC-AUC | 0.84 |

The temperature model modestly beats persistence — next-day temperature is
genuinely hard to improve on much from same-day features alone without
richer inputs (pressure trends, upstream weather systems). The rain
classifier's AUC of 0.84 shows real discriminative signal.

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # then fill in OPENWEATHER_API_KEY
python manage.py migrate
python manage.py runserver
```

### (Re)training the model

Trained artifacts are committed, so this is optional:

```bash
python manage.py build_training_dataset   # fetches from Open-Meteo, ~2 min
python manage.py train_forecast_model     # trains + writes metrics.json
```

### Running tests

```bash
python manage.py test weather
```

## Known limitations / what's next

- No automated retraining or drift monitoring — the model is a static
  snapshot from the training run above. A natural next step: log each
  forecast alongside the next day's actual outcome to measure live accuracy
  over time.
- Training features are daily-resolution (e.g. daily mean pressure); inference
  features are a single point-in-time reading. This is a documented
  approximation, not a bug.
- No authentication or per-user accounts — city tracking is session-only,
  a deliberate scope choice for a no-login demo rather than a limitation to
  "fix."
- The Quick Help widget is intentionally simple keyword matching. It is not
  branded as AI because it isn't.