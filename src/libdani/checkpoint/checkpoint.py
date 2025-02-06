import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from functools import wraps
from datetime import datetime
from typing import Any, TypeVar, Generic, Literal, Type

from loguru import logger


T = TypeVar("T")


@dataclass
class Checkpoint(Generic[T]):
    """Encapsulates user-defined state with checkpoint metadata"""

    # work state
    state: T

    # metadata
    start_from: int
    last_item: int  # Last item that was processed
    timestamp: str
    status: Literal["running", "done"]

    @classmethod
    def from_state(
        cls,
        state: T,
        last_item: int = 0,
        status: Literal["running", "done"] = "running",
    ):
        start_from = last_item + 1 if status == "running" else last_item
        return cls(
            state=state,
            start_from=start_from,
            last_item=last_item,
            timestamp=datetime.now().isoformat(),
            status=status,
        )


def checkpoint(
    StateClass: Type[T],
    filename: str = ".ckpt",
    freq: int = 1,
    log_level: str = "error",
):
    """
    Decorator that wraps a function and keeps track of execution state.
    Automatically resumes from the last checkpoint.

    :param StateClass: The user-defined state class.
    :param filename: Checkpoint file location.
    :param freq: Frequency of checkpoint saves.
    :param log_enabled: Set to False to disable logging.
    """

    def decorator(func):
        log = logger.bind(func=func.__name__)

        if log_level:
            log.remove(0)
            log.add(sys.stdout, level=log_level.upper())

        @wraps(func)
        def wrapper(*args, **kwargs):
            log.info(f"Starting function `{func.__name__}`")

            # Check and load checkpoint
            data = load_checkpoint(filename)
            if data:
                try:
                    ckpt = Checkpoint(
                        state=StateClass(**data["state"]),
                        start_from=data["last_item"] + 1,
                        last_item=data["last_item"],
                        timestamp=data["timestamp"],
                        status=data["status"],
                    )
                    log.info(f"Checkpoint loaded: {ckpt}")
                except Exception as e:
                    log.error(
                        f"Failed to load checkpoint `{filename}` due to: {e}. Resetting state."
                    )
                    ckpt = Checkpoint.from_state(StateClass())
            else:
                log.warning("No checkpoint found. Starting fresh.")
                ckpt = Checkpoint.from_state(StateClass())

            kwargs["ckpt"] = ckpt
            kwargs["state"] = ckpt.state

            # Save initial checkpoint before execution
            save_checkpoint(filename, ckpt)

            # Run the generator internally and update the state
            try:
                for _ in func(*args, **kwargs):
                    ckpt.last_item += 1

                    if ckpt.last_item % freq == 0:
                        save_checkpoint(filename, ckpt)

                # Mark as "done" when finished
                ckpt.status = "done"
                save_checkpoint(filename, ckpt)
                log.info(f"Function `{func.__name__}` completed successfully.")

            except Exception as e:
                log.error(f"Error during execution of `{func.__name__}`: {e}")
                raise

        return wrapper

    return decorator


def load_checkpoint(filename: str):
    """Load checkpoint state from a file"""
    filepath = Path(filename)
    if filepath.exists():
        try:
            return json.loads(filepath.read_text())
        except Exception:
            pass  # Ignore errors and start fresh if corrupted
    return None


def save_checkpoint(filename: str, ckpt: Checkpoint):
    """Save checkpoint state to a file"""
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data = asdict(ckpt)
    # Don't save this field
    del data["start_from"]

    filepath.write_text(json.dumps(data, indent=2))
