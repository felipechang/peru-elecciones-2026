"""Generator entry point — runs all ingestion steps in order.

Usage:
    python -m generator                    # run all steps
    python -m generator parties            # only party + summary ingestion
    python -m generator candidates         # only candidate ingestion
    python -m generator topics             # only topic extraction
"""
from __future__ import annotations

import logging
import sys

from generator.config import ConfigError, get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

STEPS = {
    "parties": "generator.ingest_parties:ingest_parties",
    "candidates": "generator.ingest_candidates:ingest_candidates",
    "topics": "generator.ingest_topics:ingest_topics",
}


def _run(step_name: str) -> None:
    module_path, func_name = STEPS[step_name].rsplit(":", 1)
    import importlib
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    log.info("=== Starting step: %s ===", step_name)
    func()
    log.info("=== Finished step: %s ===", step_name)


def main(argv: list[str] | None = None) -> None:
    try:
        get_config()
    except ConfigError as exc:
        log.error("Configuration error: %s", exc)
        sys.exit(1)

    args = (argv or sys.argv)[1:]

    if args:
        unknown = [a for a in args if a not in STEPS]
        if unknown:
            log.error("Unknown step(s): %s. Valid steps: %s", unknown, list(STEPS))
            sys.exit(1)
        requested = args
    else:
        requested = list(STEPS)

    for step in requested:
        try:
            _run(step)
        except Exception as exc:
            log.error("Step '%s' failed: %s", step, exc)
            sys.exit(1)

    log.info("Generator pipeline complete.")


if __name__ == "__main__":
    main()
