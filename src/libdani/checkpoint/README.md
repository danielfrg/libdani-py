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


For example if this function failed and was called again it would run
everything from scratch:

```python
def work():
    for i in range(100_000):
        # do work

        file.write(output)
```

Replace it with this and it will keep a checkpoint and start from where it left
off.

```python
@checkpoint
def work(ckpt):
    for i in range(ckpt.start_from, 100_000):
        # do work

        file.write(output)

# or let it handle the file for you:

@checkpoint(output="example-file.py")
def work(ckpt):
    for i in range(ckpt.start_from, 100_000):
        # do work

        yield output
```
