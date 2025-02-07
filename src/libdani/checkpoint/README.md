# checkpoint

Useful for functions that iterate over something and produce an output.
It saves a checkpoint and if the function fails it resumes from where it left off.

Features:
- Simple. Focused in code. For pipelines use airflow or similar
- Saves checkpoint to a `.ckpt.json` file
- Generator based
- Automatically detecting function changes with a hash to restar the process
- Optinal logging
- Handle output files 


For example if this function failed and would have to restart from scratch:

```
def work():
    for i in range(100_000):
        # do work

        file.write(output)
```

Replace it with

```
@checkpoint
def work(ckpt):
    for i in range(ckpt.start_from, 100_000):
        # do work
        yield output
```
