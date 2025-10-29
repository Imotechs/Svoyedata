# bank_data_fetcher.py
import httpx
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import models
from app.services import parser
from app.core.config import settings
from datetime import date

BASE_URL = settings.CBR_MORTGAGE_URL


async def resolve_xlsx_url(year: int, month: int, day: int = 1) -> str:
    """Try to find the correct XLSX download URL for a given date."""
    date_str = f"{year:04d}{month:02d}{day:02d}"
    candidate = f"{BASE_URL}01_02_Participants_e_{date_str}.xlsx"

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(candidate)
        if resp.status_code == 200:
            return candidate

        resp = await client.get(BASE_URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if "Participants_e_" in a["href"] and a["href"].endswith(".xlsx"):
                if date_str in a["href"]:
                    return a["href"] if a["href"].startswith("http") else f"https://www.cbr.ru{a['href']}"
    raise ValueError(f"No XLSX found for date {date_str}")




async def store_to_db(df: pd.DataFrame, source_url: str, report_date: date):
    async with AsyncSessionLocal() as session:
        # --- Load existing metrics and regions ---
        metrics = await session.execute(select(models.Metric))
        metric_map = {m.key: m.id for m in metrics.scalars()}

        for col in df.columns:
            if col in ["region", "federal_district"]:
                continue
            if col not in metric_map:
                display_name = col.replace("_", " ").title()
                m = models.Metric(key=col, display_name=display_name, unit="institutions")
                session.add(m)
                await session.flush()
                metric_map[col] = m.id

        regions = await session.execute(select(models.Region))
        region_map = {r.name: r.id for r in regions.scalars()}
        for _, row in df.iterrows():
            name = row["region"]
            if name not in region_map:
                r = models.Region(name=name, code=None)
                session.add(r)
                await session.flush()
                region_map[name] = r.id

        # --- Upsert values ---
        total_updated, total_inserted = 0, 0
        for _, row in df.iterrows():
            region_id = region_map[row["region"]]
            for col in df.columns:
                if col in ["region", "federal_district"]:
                    continue
                metric_id = metric_map[col]
                val = float(row[col])

                existing = await session.execute(
                    select(models.MetricValue).where(
                        models.MetricValue.metric_id == metric_id,
                        models.MetricValue.region_id == region_id,
                        models.MetricValue.date == report_date
                    )
                )
                existing_val = existing.scalar_one_or_none()

                if existing_val:
                    existing_val.value = val
                    existing_val.source_url = source_url
                    total_updated += 1
                else:
                    mv = models.MetricValue(
                        metric_id=metric_id,
                        region_id=region_id,
                        value=val,
                        date=report_date,
                        source_url=source_url,
                    )
                    session.add(mv)
                    total_inserted += 1

        await session.commit()
        print(f" Upserted {total_inserted} new values, updated {total_updated} existing.")


async def fetch_and_store(year: int, month: int, day: int = 1):
    from datetime import date
    url = await resolve_xlsx_url(year, month, day)

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    df = parser.parse_excel(resp.content)
    report_date = date(year, month, day)
    await store_to_db(df, url, report_date)

