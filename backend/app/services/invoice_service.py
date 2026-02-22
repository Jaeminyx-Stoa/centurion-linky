"""Invoice PDF generation service using ReportLab."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.clinic import Clinic
from app.models.settlement import Settlement

logger = logging.getLogger(__name__)


class InvoiceService:
    """Generates tax invoice PDFs for settlements."""

    def generate_pdf(self, settlement: Settlement, clinic: Clinic) -> bytes:
        """Generate a tax invoice PDF for a settlement."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=12,
        )
        normal_style = styles["Normal"]

        elements = []

        # Title
        elements.append(Paragraph(
            "Tax Invoice / \uc138\uae08\uacc4\uc0b0\uc11c",
            title_style,
        ))
        elements.append(Spacer(1, 10 * mm))

        # Invoice info
        period = f"{settlement.period_year}-{settlement.period_month:02d}"
        now = datetime.now(timezone.utc)
        info_data = [
            ["Invoice No.", f"INV-{period}-{str(settlement.id)[:8]}"],
            ["Issue Date", now.strftime("%Y-%m-%d")],
            ["Period", period],
        ]
        info_table = Table(info_data, colWidths=[40 * mm, 80 * mm])
        info_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10 * mm))

        # Supplier and receiver
        party_data = [
            ["Supplier (Platform)", "Receiver (Clinic)"],
            ["Centurion Medical Platform", clinic.name],
            [
                "",
                f"Business No: {clinic.business_number or 'N/A'}",
            ],
            ["", f"Address: {clinic.address or 'N/A'}"],
        ]
        party_table = Table(party_data, colWidths=[80 * mm, 80 * mm])
        party_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(party_table)
        elements.append(Spacer(1, 10 * mm))

        # Settlement details table
        def fmt(val: Decimal) -> str:
            return f"{val:,.2f}"

        detail_data = [
            ["Item", "Amount"],
            ["Total Payment Amount", fmt(settlement.total_payment_amount)],
            ["Total Payment Count", str(settlement.total_payment_count)],
            [
                f"Commission ({settlement.commission_rate}%)",
                fmt(settlement.commission_amount),
            ],
            ["VAT (10%)", fmt(settlement.vat_amount)],
            ["Total Settlement", fmt(settlement.total_settlement)],
        ]
        detail_table = Table(detail_data, colWidths=[100 * mm, 60 * mm])
        detail_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.grey),
            ("LINEBELOW", (0, -1), (-1, -1), 2, colors.black),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 15 * mm))

        # Notes
        if settlement.notes:
            elements.append(Paragraph(f"Notes: {settlement.notes}", normal_style))

        doc.build(elements)
        return buffer.getvalue()
