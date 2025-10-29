from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.db.session import get_db
from app.models import models

router = APIRouter()

@router.get("/latest")
async def get_latest_metrics(db=Depends(get_db)):
    q = select(models.MetricValue, models.Metric, models.Region) \
        .join(models.Metric) \
        .outerjoin(models.Region) \
        .order_by(models.MetricValue.date.desc()) \
        .limit(50)
    res = await db.execute(q)
    data = []
    for mv, m, r in res.all():
        data.append({
            "id": mv.id,
            "metric": m.display_name,
            "region": r.name if r else None,
            "value": mv.value,
            "date": mv.date
        })
    return {"data": data}
