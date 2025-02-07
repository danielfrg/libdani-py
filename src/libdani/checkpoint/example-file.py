"""
This example shows a very common task: saving the output of a function to a file

It writes a new line per item processed.
The values in the fle are the yielded values from the function.
"""

import sys

from libdani import checkpoint, Checkpoint

N = 10


@checkpoint(output="example-file.txt")
def work(ckpt: Checkpoint):
    for i in range(ckpt.start_from, N):
        print("Wrote to file:", i)
        yield i

        if i == 4:
            print("Expected error while processing")
            sys.exit(1)

    print("Work done")


if __name__ == "__main__":
    work()
