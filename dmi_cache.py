import os
import json
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional, Tuple

import requests

DMI_CACHE_DIR = os.environ.get("DMI_CACHE_DIR", "dmi_cache")
DMI_START_CACHE_DATE = os.environ.get("DMI_START_CACHE_DATE")
DMI_API_URL = os.environ.get("DMI_API_URL", "https://dmigw.govcloud.dk/v2/metObs/collections/observation/items")
DMI_API_KEY = os.environ.get("DMI_API_KEY")


def _ensure_cache_dir() -> None:
    os.makedirs(DMI_CACHE_DIR, exist_ok=True)


def _cache_file_path(date: datetime) -> str:
    return os.path.join(DMI_CACHE_DIR, f"{date.strftime('%Y-%m-%d')}.json")


def _is_day_cached(date: datetime) -> bool:
    return os.path.exists(_cache_file_path(date))


def _fetch_dmi_day(date: datetime) -> Optional[dict]:
    params = {
        "datetime": date.strftime("%Y-%m-%dT00:00:00Z"),
        "api-key": DMI_API_KEY,
    }
    try:
        print(f"Fetching weather data for {date.date()} from DMI")
        resp = requests.get(DMI_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        print(f"Failed fetching DMI data for {date.date()}")
        return None


def _save_day_cache(date: datetime, data: dict) -> None:
    path = _cache_file_path(date)
    with open(path, "w") as f:
        json.dump(data, f)


def update_dmi_cache() -> None:
    """Ensure cache exists from DMI_START_CACHE_DATE to today."""
    if not DMI_START_CACHE_DATE:
        return

    _ensure_cache_dir()

    start_date = datetime.fromisoformat(DMI_START_CACHE_DATE).date()
    end_date = datetime.utcnow().date()
    current = start_date
    while current <= end_date:
        if not _is_day_cached(current):
            data = _fetch_dmi_day(current)
            if data is not None:
                print(f"Caching DMI data for {current}")
                _save_day_cache(current, data)
        current += timedelta(days=1)


def _worker() -> None:
    while True:
        print("Running DMI cache update")
        update_dmi_cache()
        time.sleep(3600)


def start_dmi_cache_worker() -> None:
    if not DMI_START_CACHE_DATE:
        return
    thread = Thread(target=_worker, daemon=True)
    thread.start()


def get_cached_date_range() -> Optional[Tuple[datetime.date, datetime.date]]:
    """Return the minimum and maximum dates available in the cache.

    Scans :data:`DMI_CACHE_DIR` for ``*.json`` files.  The file names are
    expected to be in ``YYYY-MM-DD.json`` format.  If no valid cache files are
    found, ``None`` is returned.
    """

    if not os.path.isdir(DMI_CACHE_DIR):
        return None

    dates = []
    for name in os.listdir(DMI_CACHE_DIR):
        if not name.endswith(".json"):
            continue
        try:
            date = datetime.strptime(os.path.splitext(name)[0], "%Y-%m-%d").date()
            dates.append(date)
        except ValueError:
            continue

    if not dates:
        return None

    return min(dates), max(dates)
