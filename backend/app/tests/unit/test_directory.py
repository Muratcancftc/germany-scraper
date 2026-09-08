from app.scraper.sources.directory import DirectorySource


def test_parse_result_links_only_company_profiles():
    src = DirectorySource()
    html = """
    <html><body>
      <a href="/gsbiz/11111111-1111-1111-1111-111111111111">McFIT Berlin</a>
      <a href="/gsbiz/22222222-2222-2222-2222-222222222222">Basic-Fit</a>
      <a href="/branchenbuch">Branchenkatalog</a>
      <a href="/gsservice/impressum">Impressum</a>
      <a href="/suche/fitnessstudio%20berlin">Mehr Anzeigen</a>
      <a href="https://gelbeseiten.de/ratgeber/gl">Ratgeber</a>
    </body></html>
    """
    urls = src._parse_result_links(html)
    assert len(urls) == 2
    assert all("/gsbiz/" in u for u in urls)
    assert "branchenbuch" not in " ".join(urls)
    assert "impressum" not in " ".join(urls)
