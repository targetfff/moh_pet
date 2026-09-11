from time import perf_counter

from flask import g, has_request_context, request
from sqlalchemy import event

from app.extensions import db


def init_performance_logging(app):
    if not app.config.get("PERFORMANCE_LOGGING", False):
        return

    with app.app_context():
        engine = db.engine

    @app.before_request
    def start_request_timer():
        g.performance_start = perf_counter()
        g.sql_query_count = 0
        g.sql_time_ms = 0.0

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
    ):
        if not has_request_context():
            return

        g.sql_query_count = (
                getattr(g, "sql_query_count", 0) + 1
        )
        context._performance_query_start = perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
    ):
        if not has_request_context():
            return

        started_at = getattr(
            context,
            "_performance_query_start",
            None,
        )

        if started_at is None:
            return

        g.sql_time_ms = (
                getattr(g, "sql_time_ms", 0.0)
                + (perf_counter() - started_at) * 1000
        )

    @app.after_request
    def log_request_performance(response):
        if request.endpoint == "static":
            return response

        started_at = getattr(
            g,
            "performance_start",
            None,
        )

        if started_at is None:
            return response

        total_ms = (
                           perf_counter() - started_at
                   ) * 1000

        app.logger.info(
            "[PERF] %s %s | status=%s | "
            "queries=%s | sql=%.2f ms | total=%.2f ms",
            request.method,
            request.path,
            response.status_code,
            getattr(g, "sql_query_count", 0),
            getattr(g, "sql_time_ms", 0.0),
            total_ms,
        )

        return response
