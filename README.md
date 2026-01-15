# CrawlConsole (Crawl4AI Edition)

A fully working, self-hosted crawler with HTML UI, powered by [Crawl4AI](https://github.com/unclecode/crawl4ai) for JavaScript execution and advanced crawling capabilities.

## Features
- **JavaScript Rendering**: Uses Crawl4AI (Playwright) to handle dynamic websites.
- **FastAPI Backend**: Robust and fast async API.
- **SQLite Storage**: Simple, file-based persistence.
- **Extraction**: Supports CSS selectors for data extraction.
- **Control**: Concurrency, depth limits, max pages, delays, robots.txt.
- **UI**: Web interface to submit jobs and view results.

## Installation

This project is set up to use `uv` for dependency management.

1.  **Create Virtual Environment**:
    ```bash
    uv venv
    ```

2.  **Install Dependencies**:
    ```bash
    uv pip install -e .
    ```

3.  **Setup Crawl4AI (Install Browsers)**:
    ```bash
    uv run crawl4ai-setup
    ```

## Running the Server

Run the application with `uvicorn`:

```bash
uv run uvicorn app.main:app --reload
```

## Usage

1.  Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
2.  Enter seeds (URLs) and configure your job.
3.  Click "Start Job".
4.  Monitor status and download results as JSONL.

## Project Structure

- `app/`
  - `crawler.py`: Core logic using `AsyncWebCrawler` from `crawl4ai`.
  - `main.py`: FastAPI routes.
  - `models.py`: Pydantic models.
  - `db.py`: SQLite database queries.
  - `static/`: HTML UI.
- `pyproject.toml`: Project and dependency configuration.

