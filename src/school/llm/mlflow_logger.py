from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def log_experiment(config: dict[str, Any], metrics: dict[str, float],
                   artifacts: dict[str, Path], run_name: str) -> dict[str, Any]:
    try:
        import mlflow
    except ImportError:
        out = Path("out/mlflow_local")
        out.mkdir(parents=True, exist_ok=True)

        (out / f"{run_name}.json").write_text(
            json.dumps({"config": config, "metrics": metrics}, indent=2), encoding="utf-8")
        return {"backend": "local_fallback", "path": str(out / f"{run_name}.json")}

    mlflow.set_experiment("lab2-llm")
    with mlflow.start_run(run_name = run_name) as run:
        mlflow.log_params(config)
        mlflow.log_metrics(metrics)

        for name, path in artifacts.items():
            mlflow.log_artifact(str(path), artifact_path=name)
            
        return {"backend": "mlflow", "run_id": run.info.run_id}