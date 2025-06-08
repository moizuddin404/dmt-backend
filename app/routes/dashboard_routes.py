from datetime import datetime 
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.deps import get_db
from app.models.core import FileUploadLog

dashboard_router = APIRouter(tags=["Dashboard"])


@dashboard_router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_uploaded = db.query(func.count()).select_from(FileUploadLog).scalar()
    total_success = db.query(func.count()).select_from(FileUploadLog).filter(FileUploadLog.status == "processed").scalar()
    total_issues = db.query(func.count()).select_from(FileUploadLog).filter(FileUploadLog.status == "validation_error").scalar()

    success_rate = (total_success / total_uploaded * 100) if total_uploaded > 0 else 0


    return [
        {
            "title": "Total Files Uploaded",
            "value": f"{total_uploaded:,}",
            "icon": "FileText",
            "color": "text-blue-600",
            "bgColor": "bg-blue-50",
        },
        {
            "title": "Successfully Processed",
            "value": f"{total_success:,}",
            "icon": "CheckCircle",
            "color": "text-green-600",
            "bgColor": "bg-green-50",
        },
        {
            "title": "Success Rate",
            "value": f"{success_rate:.1f}%",
            "icon": "TrendingUp",
            "color": "text-purple-600",
            "bgColor": "bg-purple-50",
        },
    ]

@dashboard_router.get("/validation-summary")
def get_validation_summary(db: Session = Depends(get_db)):
    logs = db.query(FileUploadLog).all()

    total_missing = 0
    total_extra = 0
    total_empty = 0
    total_mapped = 0

    for log in logs:
        total_missing += len(log.missing_columns or [])
        total_extra += len(log.extra_columns or [])
        total_empty += log.empty_cells or 0
        total_mapped += len(log.mapped_columns or [])

    return [
        {"name": "Mapped Columns", "value": total_mapped, "color": "#059669"},
        {"name": "Missing Columns", "value": total_missing, "color": "#dc2626"},
        {"name": "Extra Columns", "value": total_extra, "color": "#ea580c"},
        {"name": "Empty Cells", "value": total_empty, "color": "#d97706"},
    ]

@dashboard_router.get("/upload-trends")
def get_upload_trends(db: Session = Depends(get_db)):
    
    query = (
        db.query(
            func.extract("year", FileUploadLog.upload_time).label("year"),
            func.extract("month", FileUploadLog.upload_time).label("month"),
            func.count(FileUploadLog.file_id).label("total_uploads"),
            func.count(
                func.nullif(FileUploadLog.status != "processed", True)
            ).label("successful_uploads"),
        )
        .group_by("year", "month")
        .order_by("year", "month")
    )

    results = query.all()

    trends = []
    for r in results:
        year = int(r.year)
        month = int(r.month)
        month_name = datetime(year, month, 1).strftime("%b")  # e.g. 'Jan'
        trends.append(
            {
                "name": month_name,
                "year": year,
                "uploads": r.total_uploads,
                "successful": r.successful_uploads,
            }
        )
    return trends