import sys
from dataclasses import dataclass

from libdani import checkpoint, Checkpoint


@dataclass
class State:
    count: int = 0


N = 10


@checkpoint(State)
def work(state: State, ckpt: Checkpoint):
    if ckpt.status == "done":
        print("Work already done")
        return

    print("Starting work from", ckpt.start_from)
    for i in range(ckpt.start_from, N):
        state.count = state.count + 1
        print("Processed:", i)
        yield

        if i == 5:
            print("Expected error while processing")
            sys.exit(1)

    return state.count


if __name__ == "__main__":
    work()
