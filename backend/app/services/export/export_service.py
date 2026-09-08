"""Export companies of a job to Excel (.xlsx) and PDF (German characters safe).

Inputs are plain dicts of company records plus the job snapshot — no database
models are involved. Companies are written exactly once (the job's result list
is already deduplicated).
"""

# ruff: noqa: E501 (long HTML/CSS template lines in string literals)

from __future__ import annotations

import os
from datetime import datetime

from fastapi import HTTPException
from fastapi.responses import FileResponse
from jinja2 import Template

from app.core.config import settings
from app.core.logging.logger import logger


class ExportService:
    def __init__(self):
        self.export_dir = os.path.abspath(settings.EXPORT_DIR)
        os.makedirs(self.export_dir, exist_ok=True)

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

    def _url(self, filename: str) -> str:
        return f"/api/exports/{filename}"

    # --- Excel ----------------------------------------------------------
    def export_excel(self, job_id: int, companies: list[dict]) -> str:
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Scraping Ergebnisse"

        headers = [
            "Firma", "Kategorie", "Telefon", "E-Mail", "Adresse", "Hausnummer",
            "PLZ", "Stadt", "Bundesland", "Website", "Quelle", "Quelle URL",
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
            ws.cell(row=idx, column=12, value=row["source_url"])

        widths = [40, 26, 18, 28, 30, 14, 12, 20, 20, 40, 18, 40]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

        filename = f"job_{job_id}_{datetime.utcnow():%Y%m%d_%H%M%S}.xlsx"
        path = os.path.join(self.export_dir, filename)
        wb.save(path)
        logger.info("Excel export done", job_id=job_id, count=len(companies))
        return self._url(filename)

    # --- PDF ------------------------------------------------------------
    def export_pdf(self, job_id: int, companies: list[dict], job: dict | None = None) -> str:
        from weasyprint import HTML

        template = Template(_PDF_TEMPLATE)
        html = template.render(
            date=datetime.utcnow().strftime("%d.%m.%Y %H:%M"),
            count=len(companies),
            cities=job.get("city_count", 0) if job else 0,
            categories=job.get("category_count", 0) if job else 0,
            companies=self._to_dicts(companies),
        )
        filename = f"job_{job_id}_{datetime.utcnow():%Y%m%d_%H%M%S}.pdf"
        path = os.path.join(self.export_dir, filename)
        HTML(string=html).write_pdf(path)
        logger.info("PDF export done", job_id=job_id, count=len(companies))
        return self._url(filename)

    # --- serving --------------------------------------------------------
    def serve(self, filename: str) -> FileResponse:
        path = os.path.join(self.export_dir, os.path.basename(filename))
        if not os.path.exists(path):
            raise HTTPException(404, "Export not found")
        return FileResponse(path, filename=filename)

export_service = ExportService()

_PDF_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: 'Liberation Sans', Arial, sans-serif; font-size: 11px; margin: 24px; color: #1e293b; }
  h1 { color: #1e3a8a; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; }
  .meta { color: #475569; margin-bottom: 16px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }
  th { background: #3b82f6; color: #fff; }
  tr:nth-child(even) { background: #f1f5f9; }
</style>
</head>
<body>
  <h1>Scraping Ergebnisse</h1>
  <p class="meta">
    Datum: {{ date }} &nbsp;|&nbsp; Städte: {{ cities }} &nbsp;|&nbsp; Kategorien: {{ categories }} &nbsp;|&nbsp; Ergebnisse: {{ count }}
  </p>
  <table>
    <thead>
      <tr>
        <th>Firma</th><th>Kategorie</th><th>Telefon</th><th>E-Mail</th><th>Adresse</th>
        <th>PLZ</th><th>Stadt</th><th>Website</th><th>Quelle</th>
      </tr>
    </thead>
    <tbody>
      {% for c in companies %}
      <tr>
        <td>{{ c.name }}</td>
        <td>{{ c.category }}</td>
        <td>{{ c.phone }}</td>
        <td>{{ c.email }}</td>
        <td>{{ c.street }} {{ c.house_number }}</td>
        <td>{{ c.postal_code }}</td>
        <td>{{ c.city }}</td>
        <td>{{ c.website }}</td>
        <td>{{ c.source }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""
