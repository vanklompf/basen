# Swimming Pool Occupancy Monitor

A dockerized web application that monitors and visualizes swimming pool occupancy at MOSIR Łańcut.

## Features

- Automatically fetches pool occupancy data (configurable interval, default: 5 minutes)
- Stores historical data in SQLite database
- Web interface with real-time charts
- RESTful API for data access
- Fully dockerized for easy deployment

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker compose up -d
```

The application will be available at `http://localhost:5000`

### Using Docker

```bash
docker build -t basen-monitor .
docker run -d -p 5000:5000 -v $(pwd)/instance:/app/instance basen-monitor
```

## API Endpoints

- `GET /` - Main web interface with chart
- `GET /api/data?hours=24` - Get historical data (default: last 24 hours)
- `GET /api/latest` - Get the most recent reading
- `GET /health` - Health check endpoint

## Configuration

The scraper fetches data from:
`http://www.mosir-lancut.pl/asp/pl_start.asp?typ=14&menu=135&strona=1`

The fetch interval is configurable via the `POLLING_INTERVAL_MINUTES` environment variable (default: 5 minutes).


## Database

The SQLite database is stored in `instance/database.db` and persists across container restarts when using volume mounts.

## Development

To run locally without Docker:

```bash
pip install -r requirements.txt
python app.py
```

## License

MIT
