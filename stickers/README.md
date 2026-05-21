# Panini World Cup Sticker Tracker

This folder contains tools to track Panini-style World Cup stickers for 48 countries and the common `FWC` / `CC` sticker sets.

* `countries.json` - list of 48 country 3-letter codes.
* `types.json` - sticker type definitions for team stickers, FWC, and CC.
* `inventory.py` - reusable inventory helpers for loading, saving, and summarizing sticker data.
* `generate_inventory.py` - create one JSON inventory file per country and a shared global inventory for FWC/CC.
* `report_missing.py` - report which stickers are still missing by country or overall.
* `api.py` - FastAPI app for updating country sticker inventory and reporting missing stickers.
* `requirements.txt` - API dependencies for FastAPI and Uvicorn.
* `country_inventory/` - generated per-country inventory files.
* `country_inventory/global_inventory.json` - shared inventory for common FWC and CC stickers.

## API usage

Run from the `stickers` folder:

```bash
cd stickers
uvicorn api:app --reload
```

Endpoints:

* `GET /countries` — list available country codes
* `GET /inventory/{country_code}` — report missing and found stickers for one country
* `POST /inventory/{country_code}` — update team sticker ownership with `{"stickers": [1, 5]}` or `{"stickers": "1,5"}`

## UI

Visit `http://127.0.0.1:8000/` after starting the app to use the local web interface.

## Notes

The API and UI both update the same per-country JSON inventory files in `country_inventory/`.
