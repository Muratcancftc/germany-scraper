from app.scraper.extractors.company_data import CompanyDataExtractor
from app.scraper.extractors.jsonld import JsonLdExtractor

HTML = """
<html>
<head>
  <title>FitX Dortmund | Fitnessstudio</title>
  <meta property="og:site_name" content="FitX Dortmund">
</head>
<body>
  <script type="application/ld+json">
  {
    "@type": "HealthClub",
    "name": "FitX Dortmund",
    "telephone": "+49 231 123456",
    "email": "info@fitx-dortmund.de",
    "url": "https://www.fitx-dortmund.de",
    "address": {
      "streetAddress": "Hauptstraße",
      "postalCode": "44135",
      "addressLocality": "Dortmund"
    }
  }
  </script>
  <h1>FitX Dortmund</h1>
  <a href="tel:+49231123456">Anrufen</a>
  <a href="mailto:info@fitx-dortmund.de">Mail</a>
</body>
</html>
"""


def test_jsonld_extraction():
    data = JsonLdExtractor().extract(HTML)
    assert data.get("name") == "FitX Dortmund"
    assert data.get("phone") == "+49 231 123456"
    assert data.get("email") == "info@fitx-dortmund.de"
    assert data.get("address", {}).get("postal_code") == "44135"


def test_combined_extraction():
    data = CompanyDataExtractor().extract(HTML)
    assert data.get("name") == "FitX Dortmund"
    assert data.get("phone") == "+49 231 123456"
