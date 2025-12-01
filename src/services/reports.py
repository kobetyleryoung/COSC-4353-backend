"""
Reports service for generating volunteer management reports.

Handles business logic for CSV and PDF report generation.
"""
from __future__ import annotations
from io import BytesIO, StringIO
from datetime import datetime
from typing import List, BinaryIO
from logging import Logger
import csv

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.domain.volunteering import VolunteerHistoryEntry
from src.domain.events import Event
from src.domain.users import UserId
from src.repositories.unit_of_work import UnitOfWorkManager


class ReportsService:
    """Service for generating reports from volunteer management data."""
    
    def __init__(self, uow_manager: UnitOfWorkManager, logger: Logger):
        self._uow_manager = uow_manager
        self._logger = logger
    
    def generate_volunteer_history_csv(self, days: int = 365) -> BytesIO:
        """
        Generate volunteer history report as CSV.
        
        Args:
            days: Number of days to include in the report (default: 365)
            
        Returns:
            BytesIO buffer containing the CSV data
        """
        with self._uow_manager.get_uow() as uow:
            # Get volunteer history entries
            entries = uow.volunteer_history.get_recent(days)
            
            # Create CSV in memory using StringIO
            string_buffer = StringIO()
            writer = csv.writer(string_buffer, lineterminator='\n')
            
            # Write header
            writer.writerow([
                "Entry ID",
                "User ID", 
                "Event ID",
                "Role",
                "Hours",
                "Date",
                "Notes"
            ])
            
            # Write data rows
            for entry in entries:
                date_str = entry.date.strftime('%Y-%m-%d') if isinstance(entry.date, datetime) else str(entry.date)
                
                writer.writerow([
                    str(entry.id.value),
                    str(entry.user_id.value),
                    str(entry.event_id.value),
                    entry.role,
                    str(entry.hours),
                    date_str,
                    entry.notes or ""
                ])
            
            # Convert to BytesIO with UTF-8 BOM for Excel compatibility
            output = BytesIO()
            output.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            output.write(string_buffer.getvalue().encode('utf-8'))
            output.seek(0)
            
            self._logger.info(f"Generated volunteer history CSV with {len(entries)} entries")
            
            return output
    
    def generate_volunteer_history_pdf(self, days: int = 365) -> BytesIO:
        """
        Generate volunteer history report as PDF.
        
        Args:
            days: Number of days to include in the report (default: 365)
            
        Returns:
            BytesIO buffer containing the PDF data
        """
        with self._uow_manager.get_uow() as uow:
            # Get volunteer history entries
            entries = uow.volunteer_history.get_recent(days)
            
            # Create PDF in memory
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Set up fonts
            pdf.setFont("Helvetica-Bold", 16)
            y_position = height - 50
            
            # Title
            pdf.drawString(50, y_position, "Volunteer History Report")
            
            # Report metadata
            pdf.setFont("Helvetica", 10)
            y_position -= 30
            pdf.drawString(50, y_position, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            y_position -= 15
            pdf.drawString(50, y_position, f"Period: Last {days} days")
            y_position -= 15
            pdf.drawString(50, y_position, f"Total Entries: {len(entries)}")
            
            # Table header
            y_position -= 30
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(50, y_position, "Date")
            pdf.drawString(120, y_position, "Role")
            pdf.drawString(220, y_position, "Hours")
            pdf.drawString(280, y_position, "User ID")
            pdf.drawString(400, y_position, "Event ID")
            
            # Draw line under header
            y_position -= 5
            pdf.line(50, y_position, width - 50, y_position)
            y_position -= 15
            
            # Table rows
            pdf.setFont("Helvetica", 8)
            for entry in entries:
                # Check if we need a new page
                if y_position < 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 8)
                    y_position = height - 50
                
                date_str = entry.date.strftime('%Y-%m-%d') if isinstance(entry.date, datetime) else str(entry.date)
                
                pdf.drawString(50, y_position, date_str)
                pdf.drawString(120, y_position, entry.role[:15])  # Truncate if too long
                pdf.drawString(220, y_position, f"{entry.hours}h")
                pdf.drawString(280, y_position, str(entry.user_id.value)[:20])
                pdf.drawString(400, y_position, str(entry.event_id.value)[:20])
                
                y_position -= 15
            
            # Finalize PDF
            pdf.save()
            buffer.seek(0)
            
            self._logger.info(f"Generated volunteer history PDF with {len(entries)} entries")
            
            return buffer
    
    def generate_events_csv(self) -> BytesIO:
        """
        Generate events report as CSV.
        
        Returns:
            BytesIO buffer containing the CSV data
        """
        with self._uow_manager.get_uow() as uow:
            # Get all events
            events = uow.events.list_all()
            
            # Create CSV in memory
            output = BytesIO()
            output.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            
            # Write header
            header = [
                "Event ID",
                "Title",
                "Description",
                "Status",
                "Location",
                "City",
                "State",
                "Required Skills",
                "Start Date",
                "End Date",
                "Capacity"
            ]
            csv_line = ','.join(f'"{field}"' for field in header) + '\n'
            output.write(csv_line.encode('utf-8'))
            
            # Write data rows
            for event in events:
                location_name = event.location.name if event.location else ""
                location_city = event.location.city if event.location else ""
                location_state = event.location.state if event.location else ""
                skills = ", ".join(event.required_skills)
                
                row = [
                    str(event.id.value),
                    event.title,
                    event.description or "",
                    event.status.name,
                    location_name,
                    location_city,
                    location_state,
                    skills,
                    event.starts_at.strftime('%Y-%m-%d %H:%M'),
                    event.ends_at.strftime('%Y-%m-%d %H:%M') if event.ends_at else "",
                    str(event.capacity) if event.capacity else ""
                ]
                
                # Properly escape CSV fields
                csv_line = ','.join(
                    f'"{field.replace(chr(34), chr(34)+chr(34))}"' if ',' in field or '"' in field else field 
                    for field in row
                ) + '\n'
                output.write(csv_line.encode('utf-8'))
            
            output.seek(0)
            self._logger.info(f"Generated events CSV with {len(events)} events")
            
            return output
    
    def generate_events_pdf(self) -> BytesIO:
        """
        Generate events report as PDF.
        
        Returns:
            BytesIO buffer containing the PDF data
        """
        with self._uow_manager.get_uow() as uow:
            # Get all events
            events = uow.events.list_all()
            
            # Create PDF in memory
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Set up fonts
            pdf.setFont("Helvetica-Bold", 16)
            y_position = height - 50
            
            # Title
            pdf.drawString(50, y_position, "Events Report")
            
            # Report metadata
            pdf.setFont("Helvetica", 10)
            y_position -= 30
            pdf.drawString(50, y_position, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            y_position -= 15
            pdf.drawString(50, y_position, f"Total Events: {len(events)}")
            
            # Table header
            y_position -= 30
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(50, y_position, "Title")
            pdf.drawString(200, y_position, "Start Date")
            pdf.drawString(300, y_position, "Location")
            pdf.drawString(450, y_position, "Status")
            
            # Draw line under header
            y_position -= 5
            pdf.line(50, y_position, width - 50, y_position)
            y_position -= 15
            
            # Table rows
            pdf.setFont("Helvetica", 8)
            for event in events:
                # Check if we need a new page
                if y_position < 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 8)
                    y_position = height - 50
                
                location = event.location.name[:30] if event.location else "N/A"
                
                pdf.drawString(50, y_position, event.title[:25])
                pdf.drawString(200, y_position, event.starts_at.strftime('%Y-%m-%d'))
                pdf.drawString(300, y_position, location)
                pdf.drawString(450, y_position, event.status.name)
                
                y_position -= 15
            
            # Finalize PDF
            pdf.save()
            buffer.seek(0)
            
            self._logger.info(f"Generated events PDF with {len(events)} events")
            
            return buffer
