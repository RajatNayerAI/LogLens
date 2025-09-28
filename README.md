# LogLens

LogLens is a command-line tool for analyzing and extracting patterns from log files. It is designed to help developers and system administrators quickly gain insights from large log datasets.

## Features
- Pattern-based log analysis using customizable patterns (see `patterns.json`)
- Supports multiple log file formats
- Export results to CSV and JSON (see `Exported/` directory)
- Sample log files included for testing (see `Logs- Sample Data/`)

## Directory Structure
```
Code/
  loglens.py         # Main CLI tool for log analysis
  patterns.json      # JSON file containing log patterns
Exported/
  exported.csv       # Sample exported results in CSV format
  exported.json      # Sample exported results in JSON format
Logs- Sample Data/
  *.log              # Sample log files for testing
```


## Running LogLens

Clone the repository or download the files:

```powershell
git clone <repo-url>
cd LogLens
```

Check available commands:

```powershell
python loglens.py --help
```

## Getting Started

### Prerequisites
- Python 3.11 or higher

### Usage
1. Install any required dependencies (if any are specified in `loglens.py`).
2. Run the main script from the `Code` directory:
  ```powershell
  cd Code
  python loglens.py --help
  ```
3. Analyze a log file:
  ```powershell
  python loglens.py analyse <path>/<log file name> -n 3 --level ERROR
  ```
4. Export results:
  - Results can be exported to CSV or JSON in the `Exported/` directory.

### Example
```powershell
python loglens.py --input "../Logs- Sample Data/prod_server.log" --pattern patterns.json --export ../Exported/exported.csv
```


## Command-Line Usage

LogLens can be used in the terminal in the following ways:

### 1. Analyze a Log File

```powershell
python loglens.py analyse <log_file_path> [--level INFO|WARN|ERROR] [--lines N] [--export exported.json|exported.csv]
```

- **Description:** Analyzes the specified log file, summarizes log levels, shows top critical issues, and can export results to JSON or CSV.

### 2. Tail a Log File

```powershell
python loglens.py tail <log_file_path> [--lines N]
```

- **Description:** Shows the last N lines of the log file (like the Unix `tail` command).

### Options
- `--level`: Filter logs by level (INFO, WARN, ERROR).
- `--lines` or `-n`: Number of lines or top issues to display (default: 10).
- `--export`: Export analysis results to a file (JSON or CSV).

### Example Commands

Analyze a log file and show top 5 errors:
```powershell
python loglens.py analyse "../Logs- Sample Data/prod_server.log" --level ERROR --lines 5
```

Tail the last 20 lines of a log file:
```powershell
python loglens.py tail "../Logs- Sample Data/dev_server.log" --lines 20
```

Export analysis results to CSV:
```powershell
python loglens.py analyse "../Logs- Sample Data/prod_server.log" --export ../Exported/exported.csv
```

## Customizing Patterns
- Edit `patterns.json` to add or modify log patterns for your specific use case.

