from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from io import BytesIO
import csv
from reportlab.pdfgen import canvas
from uuid import UUID
from src.services.volunteer_history import VolunteerHistoryService
from src.services.event_management import EventManagementService
from functools import lru_cache
from src.config.logging_config import logger

router = APIRouter(prefix="/reports", tags=["reports"])

# Singleton services (temporary until DB connected)
@lru_cache(maxsize=1)
def get_history_service() -> VolunteerHistoryService:
    return VolunteerHistoryService(logger)

@lru_cache(maxsize=1)
def get_event_service() -> EventManagementService:
    # Provide dummy session if needed or actual DB session
    return EventManagementService(None, logger)

# --- CSV Export ---
@router.get("/export/csv")
async def export_csv(
    history_service: VolunteerHistoryService = Depends(get_history_service)
):
    """Export all volunteer history as CSV."""
    try:
        entries = history_service.get_recent_history(days=365)  # last year
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "User ID", "Event ID", "Role", "Hours", "Date", "Notes"])
        for e in entries:
            writer.writerow([e.id.value, e.user_id.value, e.event_id.value, e.role, e.hours, e.date, e.notes or ""])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=volunteer_history.csv"}
        )
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(status_code=500, detail="CSV export failed")

# --- PDF Export ---
@router.get("/export/pdf")
async def export_pdf(
    history_service: VolunteerHistoryService = Depends(get_history_service)
):
    """Export volunteer history as PDF."""
    try:
        entries = history_service.get_recent_history(days=365)
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont("Helvetica", 12)
        y = 800
        p.drawString(50, y, "Volunteer History Report")
        y -= 30
        for e in entries:
            line = f"{e.date} | {e.user_id.value} | {e.event_id.value} | {e.role} | {e.hours}h"
            p.drawString(50, y, line)
            y -= 20
            if y < 50:
                p.showPage()
                y = 800
        p.save()
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=volunteer_history.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail="PDF export failed")
