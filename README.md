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
pip install -r requirements.txt
uvicorn api:app --reload
```

For Firestore-backed multi-user mode, set the storage provider and Firebase credentials:

```bash
cd stickers
export STORAGE_PROVIDER=firestore
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
uvicorn api:app --reload
```

When running in Firestore mode, protected API routes must receive a valid Firebase ID token in the `Authorization` header:

```
Authorization: Bearer <firebase-id-token>
```

Endpoints:

* `GET /countries` — list available country codes
* `GET /inventory/{country_code}` — report missing and found stickers for one country
* `POST /inventory/{country_code}` — bulk update ownership with `{"stickers": "MEX1,MEX5"}`
* `PATCH /inventory/{country_code}/sticker` — update a single sticker's absolute count with `{"sticker_id": "MEX1", "count": 2}`

## UI

Visit `http://127.0.0.1:8000/` after starting the app to use the local web interface.

### Features
* **Interactive Grid**: View all stickers for a selected country in a responsive grid.
* **Live Counters**: Use `+` and `-` buttons to update sticker counts in real-time.
* **Visual Tracking**: Stickers are color-coded (Red: Missing, Green: Owned, Yellow: Extras) to easily identify progress and swap opportunities.
* **Duplicate Summary**: View a detailed list of extra stickers and total counts for each country.
