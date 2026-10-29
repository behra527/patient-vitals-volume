"""Record patient vitals on a volume and read clinic settings from a bind mount."""

import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

DATA_FILE = os.environ.get("DATA_FILE", "/data/vitals.json")
CONFIG_FILE = os.environ.get("CONFIG_FILE", "/config/clinic.json")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

DEFAULT_CONFIG = {
    "clinic_name": "City Care Clinic",
    "department": "Vitals Desk",
}

_lock = Lock()


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_config():
    if not os.path.isfile(CONFIG_FILE):
        return {**DEFAULT_CONFIG, "source": "image default"}
    with open(CONFIG_FILE, encoding="utf-8") as handle:
        data = json.load(handle)
    name = str(data.get("clinic_name", "")).strip()
    department = str(data.get("department", "")).strip()
    if not name or not department:
        raise ValueError("clinic.json needs clinic_name and department")
    return {
        "clinic_name": name,
        "department": department,
        "source": "bind mount",
    }


def load_records():
    if not os.path.isfile(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("vitals file must be a list")
    return data


def save_records(records):
    folder = os.path.dirname(DATA_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)
    temporary = DATA_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)
        handle.write("\n")
    os.replace(temporary, DATA_FILE)


def require_number(body, key, low, high):
    if key not in body:
        raise ValueError(f"{key} is required")
    value = body[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    if not low <= float(value) <= high:
        raise ValueError(f"{key} must be between {low} and {high}")
    return float(value) if isinstance(value, float) else int(value)


def build_record(body):
    if not isinstance(body, dict):
        raise ValueError("body must be a JSON object")
    patient_id = str(body.get("patient_id", "")).strip()
    if not patient_id or len(patient_id) > 32:
        raise ValueError("patient_id is required and must be 32 characters or fewer")
    return {
        "patient_id": patient_id,
        "heart_rate": require_number(body, "heart_rate", 30, 220),
        "temperature": require_number(body, "temperature", 34, 42),
        "systolic_bp": require_number(body, "systolic_bp", 70, 220),
        "diastolic_bp": require_number(body, "diastolic_bp", 40, 140),
        "spo2": require_number(body, "spo2", 50, 100),
        "recorded_at": utc_now(),
    }


def summary(records):
    if not records:
        return {"count": 0}
    def avg(key):
        return round(sum(item[key] for item in records) / len(records), 2)
    return {
        "count": len(records),
        "average_heart_rate": avg("heart_rate"),
        "average_temperature": avg("temperature"),
        "average_systolic_bp": avg("systolic_bp"),
        "average_spo2": avg("spo2"),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}")

    def _send(self, status, payload):
        raw = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 100_000:
            raise ValueError("request body is missing or too large")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            config = load_config()
            self._send(200, {
                "name": "Patient Vitals Volume API",
                "clinic_name": config["clinic_name"],
                "data_file": DATA_FILE,
                "config_source": config["source"],
            })
            return
        if path == "/health":
            self._send(200, {"status": "ok"})
            return
        if path == "/config":
            self._send(200, load_config())
            return
        if path == "/vitals":
            with _lock:
                records = load_records()
            self._send(200, {"count": len(records), "records": records})
            return
        if path == "/vitals/summary":
            with _lock:
                records = load_records()
            self._send(200, summary(records))
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/vitals":
            self._send(404, {"error": "not found"})
            return
        try:
            record = build_record(self._read_json())
            with _lock:
                records = load_records()
                records.append(record)
                save_records(records)
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            self._send(400, {"error": str(exc)})
            return
        self._send(201, record)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"listening on {HOST}:{PORT}")
    print(f"data file: {DATA_FILE}")
    print(f"config file: {CONFIG_FILE}")
    server.serve_forever()


if __name__ == "__main__":
    main()
