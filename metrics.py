"""
metrics.py —
Prometheus metrics for monitoring ReFrame bot.
Exposes /metrics endpoint via a lightweight HTTP server.
"""

import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import FEATURE_FLAGS

logger = logging.getLogger(__name__)

# ── Counters ───────────────────────────────────────────────────────────────────
_commands_total = {}       # command -> count
_files_processed = {}     # type -> count
_files_failed = {}        # type -> count
_scan_threats = {}        # threat -> count

# ── Gauges ─────────────────────────────────────────────────────────────────────
_active_jobs = 0
_active_users = 0

# ── Histograms ─────────────────────────────────────────────────────────────────
_processing_times = []    # list of floats


def inc_command(command: str):
    if not FEATURE_FLAGS.get("enable_metrics"):
        return
    _commands_total[command] = _commands_total.get(command, 0) + 1


def inc_files_processed(media_type: str):
    if not FEATURE_FLAGS.get("enable_metrics"):
        return
    _files_processed[media_type] = _files_processed.get(media_type, 0) + 1


def inc_files_failed(media_type: str):
    if not FEATURE_FLAGS.get("enable_metrics"):
        return
    _files_failed[media_type] = _files_failed.get(media_type, 0) + 1


def inc_scan_threat(threat: str):
    if not FEATURE_FLAGS.get("enable_metrics"):
        return
    _scan_threats[threat] = _scan_threats.get(threat, 0) + 1


def set_active_jobs(n: int):
    global _active_jobs
    _active_jobs = n


def set_active_users(n: int):
    global _active_users
    _active_users = n


def record_processing_time(seconds: float):
    if not FEATURE_FLAGS.get("enable_metrics"):
        return
    _processing_times.append(seconds)
    if len(_processing_times) > 10000:
        _processing_times.pop(0)


def _render_metrics() -> str:
    lines = []
    lines.append("# HELP reframe_commands_total Total commands received")
    lines.append("# TYPE reframe_commands_total counter")
    for cmd, count in _commands_total.items():
        lines.append(f'reframe_commands_total{{command="{cmd}"}} {count}')

    lines.append("# HELP reframe_files_processed Total files processed successfully")
    lines.append("# TYPE reframe_files_processed counter")
    for mt, count in _files_processed.items():
        lines.append(f'reframe_files_processed{{type="{mt}"}} {count}')

    lines.append("# HELP reframe_files_failed Total files that failed processing")
    lines.append("# TYPE reframe_files_failed counter")
    for mt, count in _files_failed.items():
        lines.append(f'reframe_files_failed{{type="{mt}"}} {count}')

    lines.append("# HELP reframe_scan_threats Total threats detected")
    lines.append("# TYPE reframe_scan_threats counter")
    for threat, count in _scan_threats.items():
        lines.append(f'reframe_scan_threats{{threat="{threat}"}} {count}')

    lines.append("# HELP reframe_active_jobs Currently processing jobs")
    lines.append("# TYPE reframe_active_jobs gauge")
    lines.append(f"reframe_active_jobs {_active_jobs}")

    lines.append("# HELP reframe_active_users Currently active users")
    lines.append("# TYPE reframe_active_users gauge")
    lines.append(f"reframe_active_users {_active_users}")

    if _processing_times:
        avg = sum(_processing_times) / len(_processing_times)
        lines.append("# HELP reframe_processing_time_seconds Processing time")
        lines.append("# TYPE reframe_processing_time_seconds summary")
        lines.append(f"reframe_processing_time_seconds{{quantile=\"0.5\"}} {sorted(_processing_times)[len(_processing_times)//2]:.3f}")
        lines.append(f"reframe_processing_time_seconds{{quantile=\"0.95\"}} {sorted(_processing_times)[int(len(_processing_times)*0.95)]:.3f}")
        lines.append(f"reframe_processing_time_seconds{{quantile=\"0.99\"}} {sorted(_processing_times)[int(len(_processing_times)*0.99)]:.3f}")
        lines.append(f"reframe_processing_time_seconds_sum {sum(_processing_times):.3f}")
        lines.append(f"reframe_processing_time_seconds_count {len(_processing_times)}")

    lines.append(f"reframe_up 1")
    return "\n".join(lines) + "\n"


class _MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            body = _render_metrics().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/healthz":
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress request logs


def start_metrics_server(port: int = 9090):
    if not FEATURE_FLAGS.get("enable_metrics"):
        return
    def _run():
        try:
            server = HTTPServer(("0.0.0.0", port), _MetricsHandler)
            logger.info(f"Metrics server started on port {port}")
            server.serve_forever()
        except Exception as exc:
            logger.error(f"Metrics server failed: {exc}")
    t = threading.Thread(target=_run, daemon=True)
    t.start()
