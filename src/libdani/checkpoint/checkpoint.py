import sys
import json
from pathlib import Path
from functools import wraps
from datetime import datetime
from dataclasses import dataclass, asdict
from inspect import signature, Parameter
from typing import Optional, TypeVar, Generic, Literal, Type

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
        return cls(
            state=state,
            start_from=last_item,
            last_item=last_item,
            timestamp=datetime.now().isoformat(),
            status=status,
        )


def checkpoint(
    StateClass: Optional[Type[T]] = None,
    output: Optional[str | Path] = None,
    filename: str = ".ckpt",
    freq: int = 1,
    log_level: str = "error",
):
    """
    Decorator that wraps a function and keeps track of execution state.
    Automatically resumes from the last checkpoint.

    :param output: Path to the output file where the results will be saved.
    :param StateClass: The user-defined state class.
    :param filename: Checkpoint file location.
    :param freq: Frequency of checkpoint saves.
    :param log_level: Log level for the logger.
    """

    def decorator(func):
        log = logger.bind(func=func.__name__)

        if log_level:
            log.remove(0)
            log.add(sys.stdout, level=log_level.upper())

        func_signature = signature(func)
        func_params = func_signature.parameters

        @wraps(func)
        def wrapper(*args, **kwargs):
            log.info(f"Starting function `{func.__name__}`")

            # Check and load checkpoint
            data = load_checkpoint(filename)
            if data:
                try:
                    state = StateClass(**data["state"]) if data["state"] else None
                    ckpt = Checkpoint(
                        state=state,
                        start_from=data["last_item"],
                        last_item=data["last_item"],
                        timestamp=data["timestamp"],
                        status=data["status"],
                    )
                    log.info(f"Checkpoint loaded: {ckpt}")
                except Exception as e:
                    log.error(
                        f"Failed to load checkpoint `{filename}` due to: {e}. Resetting state."
                    )
                    data = StateClass() if StateClass else None
                    ckpt = Checkpoint.from_state(data)
            else:
                log.warning("No checkpoint found. Starting fresh.")
                data = StateClass() if StateClass else None
                ckpt = Checkpoint.from_state(data)

            kwargs["ckpt"] = ckpt
            kwargs["state"] = ckpt.state

            # Filter kwargs to only include parameters that exist in the function signature
            filtered_kwargs = {}
            for param_name, param in func_params.items():
                if param_name in kwargs:
                    filtered_kwargs[param_name] = kwargs[param_name]
                elif param.default is Parameter.empty and param.kind not in (
                    Parameter.VAR_POSITIONAL,
                    Parameter.VAR_KEYWORD,
                ):
                    log.warning(f"Required parameter '{param_name}' not provided")

            # Save initial checkpoint before execution
            save_checkpoint(filename, ckpt)

            # Run the generator internally and update the state
            try:
                for value in func(*args, **filtered_kwargs):
                    if value is not None:
                        print(value)
                        with open(output, "a") as f:
                            f.write(f"{value}\n")

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
