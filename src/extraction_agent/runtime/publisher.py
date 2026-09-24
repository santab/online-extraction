from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def publish_resolution(resolution: dict, *, sink: str = "log") -> None:
    """This module's job ends at publishing resolution.json — picking it up
    and routing it to a person is a separate, event-driven system out of
    scope for this repo (see architecture doc's human-in-the-loop boundary).

    TODO(prod): replace with a real publish call (queue/topic client) once
    that system's contract is defined.
    """
    if sink == "log":
        logger.info("resolution.json ready: %s", json.dumps(resolution, default=str))
        return
    raise ValueError(f"unknown publish sink {sink!r}")
