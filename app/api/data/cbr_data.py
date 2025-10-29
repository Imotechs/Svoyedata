from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi import Query, HTTPException
from app.models import models
from app.core.config import settings
from app.services.fetcher import fetch_and_store
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from datetime import date


router = APIRouter(prefix="/cbr", tags=["cbr Data"])

@router.get("/fetch")
async def fetch_data(
    year: int = Query(..., ge=2018, le=2030),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(1, ge=1, le=31)
):
    """Fetch and store data only if not already stored for the given date."""
    from datetime import date
    report_date = date(year, month, day)

    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(models.MetricValue)
            .where(models.MetricValue.date == report_date)
            .limit(1)
        )
        if existing.scalar():
            return {
                "message": f" Data for {report_date} already exists — no need to fetch again.",
                "report_date": report_date,
                "source": "local database"
            }

    # If no data for this date — fetch from CBR
    try:
        await fetch_and_store(year, month, day)
        return {
            "message": f" Fresh data fetched and stored for {report_date}",
            "report_date": report_date,
            "source": "Bank of Russia"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(models.Metric))
        metrics = result.scalars().all()
        return [
            {"id": m.id, "key": m.key, "display_name": m.display_name, "unit": m.unit}
            for m in metrics
        ]
        
@router.get("/regions")
async def get_regions():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(models.Region))
        regions = result.scalars().all()
        return [
            {"id": r.id, "name": r.name, "code": r.code}
            for r in regions
        ]



from fastapi import Path


@router.get("/trend/{metric_key}")
async def get_metric_trend(metric_key: str = Path(..., description="Metric key to view trend over time")):
    """
    Return historical values of a given metric across all available dates.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(models.MetricValue.date, models.MetricValue.value)
            .join(models.Metric)
            .where(models.Metric.key == metric_key)
            .order_by(models.MetricValue.date)
        )
        rows = result.all()

        if not rows:
            return {"metric": metric_key, "trend": []}

        trend = [{"date": r.date.isoformat(), "value": r.value} for r in rows]
        return {"metric": metric_key, "trend": trend}


@router.get("/data")
async def get_data(
    region: str | None = Query(None, description="Filter by region name"),
    metric_key: str | None = Query(None, description="Filter by metric key"),
    group_by: str | None = Query(None, description="Group results by 'region' or 'metric'"),
    date_: date | None = Query(None, description="Filter by report date"),
    aggregate: bool = Query(False, description="If true, return average per group")
):
    """
    Fetch metric values with region + metric metadata for a given report date.
    Supports filtering, grouping, and aggregation.
    """

    async with AsyncSessionLocal() as session:
        q = select(models.MetricValue).options(
            selectinload(models.MetricValue.metric),
            selectinload(models.MetricValue.region),
        )

        # --- Always prefer most recent report if no date is specified ---
        if not date_:
            latest_date_result = await session.execute(
                select(func.max(models.MetricValue.date))
            )
            latest_date = latest_date_result.scalar()
            date_ = latest_date

        q = q.where(models.MetricValue.date == date_)

        # --- Safe filters without duplicate joins ---
        if region:
            q = q.where(models.MetricValue.region.has(name=region))
        if metric_key:
            q = q.where(models.MetricValue.metric.has(key=metric_key))

        # Ensure we only get distinct values (avoid inflated joins)
        q = q.distinct()

        result = await session.execute(q)
        values = result.scalars().all()

        if not values:
            return {"count": 0, "data": [], "date": date_}

        # --- Optional aggregation ---
        if aggregate and group_by in ("region", "metric"):
            grouped = {}
            for v in values:
                key = v.region.name if group_by == "region" else v.metric.display_name
                grouped.setdefault(key, []).append(v.value)

            agg_result = [
                {
                    "group": key,
                    "average_value": round(sum(vals) / len(vals), 2),
                    "unit": v.metric.unit if v.metric else "",
                    "count": len(vals),
                }
                for key, vals in grouped.items()
            ]
            return {"count": len(agg_result), "group_by": group_by, "data": agg_result, "date": date_}

        # --- Raw data response ---
        data = [
            {
                "region": v.region.name if v.region else None,
                "region_id": v.region_id,
                "metric_key": v.metric.key,
                "metric_name": v.metric.display_name,
                "metric_id": v.metric_id,
                "unit": v.metric.unit,
                "value": v.value,
                "date": v.date,
                "source_url": v.source_url,
            }
            for v in values
        ]

        return {"count": len(data), "date": date_, "data": data}
