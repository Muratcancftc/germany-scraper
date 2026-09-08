"""Stateless export of company records to Excel (.xlsx) and PDF.

Companies come in via the request body (the frontend holds the live results
because Vercel Functions are stateless). Export is a single request/response —
the file bytes are returned directly, nothing is written to disk.

- Excel: openpyxl (pure Python)
- PDF:   ReportLab (pure Python, no system libs — works on Vercel)
"""

from __future__ import annotations

from io import BytesIO

from fastapi.responses import StreamingResponse

from app.core.logging.logger import logger


class ExportService:
    def _to_dicts(self, companies: list[dict]) -> list[dict]:
        return [
            {
                "name": c.get("name") or "-",
                "phone": c.get("phone") or "-",
                "email": c.get("email") or "-",
                "website": c.get("website") or "-",
                "street": c.get("street") or "",
                "house_number": c.get("house_number") or "",
                "postal_code": c.get("postal_code") or "",
                "city": c.get("city") or "",
                "state": c.get("state") or "",
                "category": c.get("category") or "",
                "source": c.get("source") or "",
            }
            for c in companies
        ]

    # --- Excel ----------------------------------------------------------
    def export_excel(self, companies: list[dict]) -> StreamingResponse:
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Scraping Ergebnisse"

        headers = [
            "Firma", "Kategorie", "Telefon", "E-Mail", "Adresse", "Hausnummer",
            "PLZ", "Stadt", "Bundesland", "Website", "Quelle",
        ]
        header_fill = PatternFill(start_color="3b82f6", end_color="3b82f6", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        rows = self._to_dicts(companies)
        for idx, row in enumerate(rows, 2):
            ws.cell(row=idx, column=1, value=row["name"])
            ws.cell(row=idx, column=2, value=row["category"])
            ws.cell(row=idx, column=3, value=row["phone"])
            ws.cell(row=idx, column=4, value=row["email"])
            ws.cell(row=idx, column=5, value=row["street"])
            ws.cell(row=idx, column=6, value=row["house_number"])
            ws.cell(row=idx, column=7, value=row["postal_code"])
            ws.cell(row=idx, column=8, value=row["city"])
            ws.cell(row=idx, column=9, value=row["state"])
            ws.cell(row=idx, column=10, value=row["website"])
            ws.cell(row=idx, column=11, value=row["source"])

        widths = [40, 26, 18, 28, 30, 14, 12, 20, 20, 40, 18]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        logger.info("Excel export done", count=len(companies))
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=scraping_ergebnisse.xlsx"},
        )

    # --- PDF ------------------------------------------------------------
    def export_pdf(self, companies: list[dict]) -> StreamingResponse:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(A4),
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleDE", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#1e3a8a")
        )
        meta_style = ParagraphStyle(
            "MetaDE", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#475569")
        )
        cell_style = ParagraphStyle(
            "CellDE", parent=styles["Normal"], fontSize=7.5, leading=9
        )
        header_style = ParagraphStyle(
            "HeadDE", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.white
        )

        rows = self._to_dicts(companies)
        story = [
            Paragraph("Scraping Ergebnisse", title_style),
            Spacer(1, 6),
            Paragraph(
                f"Ergebnisse: {len(rows)}  |  Stand: exportiert am heutigen Tag",
                meta_style,
            ),
            Spacer(1, 10),
        ]

        data = [[Paragraph(h, header_style) for h in (
            "Firma", "Kategorie", "Telefon", "E-Mail", "Adresse", "PLZ", "Stadt", "Website"
        )]]
        for r in rows:
            data.append([
                Paragraph(r["name"], cell_style),
                Paragraph(r["category"], cell_style),
                Paragraph(r["phone"], cell_style),
                Paragraph(r["email"], cell_style),
                Paragraph(f"{r['street']} {r['house_number']}".strip(), cell_style),
                Paragraph(r["postal_code"], cell_style),
                Paragraph(r["city"], cell_style),
                Paragraph(r["website"], cell_style),
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(table)

        doc.build(story)
        buf.seek(0)
        logger.info("PDF export done", count=len(companies))
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=scraping_ergebnisse.pdf"},
        )


export_service = ExportService()
