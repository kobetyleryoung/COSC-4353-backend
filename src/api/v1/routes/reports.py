from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import datetime

from src.services.reports import ReportsService
from src.repositories.database import get_uow, get_uow_manager
from src.repositories.unit_of_work import UnitOfWorkManager
from src.config.logging_config import logger

router = APIRouter(prefix="/reports", tags=["reports"])

#region helpers

def _get_reports_service(uow_manager: UnitOfWorkManager = Depends(get_uow_manager)) -> ReportsService:
    return ReportsService(uow_manager, logger)

#endregion

#region routes

@router.get("/volunteer-history/csv")
async def export_volunteer_history_csv(
    days: int = 365,
    reports_service: ReportsService = Depends(_get_reports_service)
):
    """Export volunteer history as CSV file."""
    try:
        csv_buffer = reports_service.generate_volunteer_history_csv(days=days)
        
        # Generate filename with current date
        filename = f"volunteer_history_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            csv_buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting volunteer history CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export volunteer history as CSV"
        )


@router.get("/volunteer-history/pdf")
async def export_volunteer_history_pdf(
    days: int = 365,
    reports_service: ReportsService = Depends(_get_reports_service)
):
    """Export volunteer history as PDF file."""
    try:
        pdf_buffer = reports_service.generate_volunteer_history_pdf(days=days)
        
        # Generate filename with current date
        filename = f"volunteer_history_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting volunteer history PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export volunteer history as PDF"
        )


@router.get("/events/csv")
async def export_events_csv(
    reports_service: ReportsService = Depends(_get_reports_service)
):
    """Export all events as CSV file."""
    try:
        csv_buffer = reports_service.generate_events_csv()
        
        # Generate filename with current date
        filename = f"events_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            csv_buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting events CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export events as CSV"
        )


@router.get("/events/pdf")
async def export_events_pdf(
    reports_service: ReportsService = Depends(_get_reports_service)
):
    """Export all events as PDF file."""
    try:
        pdf_buffer = reports_service.generate_events_pdf()
        
        # Generate filename with current date
        filename = f"events_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting events PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export events as PDF"
        )

#endregion


