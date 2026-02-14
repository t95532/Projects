# End-to-End Data Science Lifecycle with MLOps (Localhost)

## Project Overview

This project demonstrates a **complete machine learning lifecycle** using modern **MLOps tools**, running entirely on **localhost**.

It covers:

* Data versioning
* Automated pipelines
* Experiment tracking
* Model registry
* API deployment
* Monitoring and metrics

The goal is to simulate a **production-style ML system** using only local resources.

---

## Architecture

```
Raw Data
   ↓
Data Versioning (DVC)
   ↓
Preprocessing
   ↓
Feature Engineering
   ↓
Model Training (Scikit-learn)
   ↓
Experiment Tracking (MLflow)
   ↓
Model Registry
   ↓
FastAPI Model Service
   ↓
Monitoring (Prometheus + Grafana)
```

---

## Tech Stack

| Stage                  | Tool                 |
| ---------------------- | -------------------- |
| Programming            | Python               |
| Data processing        | Pandas, NumPy        |
| Modeling               | Scikit-learn         |
| Data versioning        | DVC                  |
| Experiment tracking    | MLflow               |
| Workflow orchestration | Prefect / Airflow    |
| Model serving          | FastAPI              |
| Containerization       | Docker               |
| Monitoring             | Prometheus + Grafana |

---

## Project Structure

```
mlops-advanced/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── data/
│   │   └── preprocess.py
│   ├── features/
│   │   └── build_features.py
│   ├── models/
│   │   ├── train.py
│   │   └── evaluate.py
│   └── pipeline/
│       └── airflow_dag.py
│
├── app/
│   └── main.py
│
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│
├── dvc.yaml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd mlops-advanced
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step-by-Step Pipeline Execution

### Step 1: Initialize DVC

```bash
git init
dvc init
dvc add data/raw/dataset.csv
git add .
git commit -m "Initial dataset version"
```

---

### Step 2: Run preprocessing

```bash
python src/data/preprocess.py
```

---

### Step 3: Train the model with MLflow

```bash
python src/models/train.py
```

---

### Step 4: Launch MLflow UI

```bash
mlflow ui
```

Open:

```
http://localhost:5000
```

---

### Step 5: Start the API

```bash
uvicorn app.main:app --reload
```

Open:

```
http://localhost:8000/docs
```

---

## Running Full Stack with Docker

Start all services:

```bash
docker-compose up --build
```

### Access services

| Service      | URL                        |
| ------------ | -------------------------- |
| MLflow UI    | http://localhost:5000      |
| FastAPI docs | http://localhost:8000/docs |
| Airflow UI   | http://localhost:8080      |
| Grafana      | http://localhost:3000      |

---

## Example Prediction Request

POST request to:

```
http://localhost:8000/predict
```

Example JSON:

```json
{
  "feature1": 10,
  "feature2": 5
}
```

---

## Monitoring

Prometheus collects:

* API request count
* Latency
* Error rates
* Prediction metrics

Grafana provides dashboards for:

* Model performance
* System health
* Data drift indicators

---

## Demonstration Flow

1. Update dataset → new DVC version
2. Run pipeline
3. New experiment appears in MLflow
4. Register best model
5. Deploy model via FastAPI
6. Monitor metrics in Grafana

---

## Future Improvements

* CI/CD with GitHub Actions
* Automated retraining
* Feature store integration
* Cloud deployment

---

## Author

Your Name
MLOps / Data Science Project
