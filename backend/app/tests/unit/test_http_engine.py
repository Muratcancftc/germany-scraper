from app.scraper.engines.http_engine import HttpEngine


def test_challenge_detection():
    assert HttpEngine._looks_like_challenge("Just a moment...") is True
    assert HttpEngine._looks_like_challenge("Checking your browser before accessing") is True
    assert HttpEngine._looks_like_challenge("Enable JavaScript and cookies to continue") is True
    assert HttpEngine._looks_like_challenge("") is True
    assert (
        HttpEngine._looks_like_challenge(
            "<html><body><h1>Fitnessstudio Dortmund</h1></body></html>"
        )
        is False
    )


def test_browser_used_flag_resets():
    engine = HttpEngine()
    assert engine.browser_used() is False
