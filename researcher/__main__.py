"""Researcher entry point.

Usage:
    python -m researcher          # run once, then loop on the configured schedule
    python -m researcher --once   # run a single pipeline pass and exit
"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from researcher.config import ConfigError, get_config
from researcher.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Researcher — automated candidate news pipeline"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single pipeline pass and exit (no scheduling loop).",
    )
    args = parser.parse_args(argv)

    try:
        cfg = get_config()
    except ConfigError as exc:
        log.error("Configuration error: %s", exc)
        sys.exit(1)

    if args.once:
        log.info("Running researcher pipeline (single pass).")
        try:
            run_pipeline()
        except Exception as exc:
            log.error("Pipeline failed: %s", exc, exc_info=True)
            sys.exit(1)
        return

    log.info(
        "Starting researcher scheduler — interval: %ds (%dm)",
        cfg.schedule_interval,
        cfg.schedule_interval // 60,
    )

    while True:
        try:
            run_pipeline()
        except Exception as exc:
            log.error("Pipeline run failed: %s", exc, exc_info=True)

        log.info("Next run in %d seconds.", cfg.schedule_interval)
        time.sleep(cfg.schedule_interval)


if __name__ == "__main__":
    main()
