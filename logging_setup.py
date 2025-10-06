import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime

# Context variable for correlation / request id
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        rid = None
        try:
            rid = request_id_ctx.get()
        except Exception:
            rid = None
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__
        # attempt to enrich with trace/span ids if OpenTelemetry context available
        try:  # pragma: no cover
            from opentelemetry import trace  # type: ignore

            span = trace.get_current_span()
            ctx = span.get_span_context() if span else None
            if ctx and ctx.is_valid:
                payload["trace_id"] = format(ctx.trace_id, "032x")
                payload["span_id"] = format(ctx.span_id, "016x")
        except Exception:
            pass
        for k in ("user", "username", "kid"):
            if k in record.__dict__:
                payload[k] = record.__dict__[k]
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO", json_logging: bool = True):
    if os.getenv("LOG_FORMAT", "plain").lower() == "json":
        root = logging.getLogger()
        root.handlers.clear()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonLogFormatter())
        root.addHandler(handler)
        root.setLevel(getattr(logging, level.upper(), logging.INFO))
    else:
        root = logging.getLogger()
        root.handlers.clear()
        numeric = getattr(logging, level.upper(), logging.INFO)
        root.setLevel(numeric)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root.addHandler(handler)
    # Reduce noisy libraries if desired
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    return root


__all__ = ["configure_logging", "request_id_ctx"]
