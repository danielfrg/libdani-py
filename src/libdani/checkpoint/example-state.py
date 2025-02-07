"""
This example shows how to integrate the checkpoint to a State dataclass.
The state is saved as part of the checkpoint and used to resume the work.
"""

import sys
from dataclasses import dataclass

from libdani import checkpoint, Checkpoint


@dataclass
class State:
    count: int = 0


N = 10


@checkpoint(State)
def work(state: State, ckpt: Checkpoint):
    # This if is not needed but it's good to have a base case
    if ckpt.status == "done":
        print("Work already done")
        return

    print("Starting work from", ckpt.start_from)
    for i in range(ckpt.start_from, N):
        state.count = state.count + 1
        print("Processed:", i)
        yield

        if i == 4:
            print("Expected error while processing")
            sys.exit(1)

    return state.count


if __name__ == "__main__":
    work()
