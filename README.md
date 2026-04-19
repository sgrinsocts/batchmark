# batchmark

A CLI tool for benchmarking batch jobs with configurable concurrency and reporting.

## Installation

```bash
pip install batchmark
```

## Usage

Run a benchmark against a batch job with configurable workers and iterations:

```bash
batchmark run --workers 4 --iterations 100 --job "python process.py"
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--workers` | `1` | Number of concurrent workers |
| `--iterations` | `10` | Total number of job executions |
| `--job` | required | Shell command to benchmark |
| `--output` | `stdout` | Report output format (`json`, `csv`, `table`) |

### Example Output

```
Benchmark Results
-----------------
Workers      : 4
Iterations   : 100
Total Time   : 12.43s
Avg Latency  : 0.497s
Throughput   : 8.04 jobs/sec
P95 Latency  : 0.821s
```

Export results to JSON:

```bash
batchmark run --workers 8 --iterations 200 --job "curl http://api/task" --output json > results.json
```

## License

MIT © batchmark contributors