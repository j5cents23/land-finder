import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from scraper.models import Listing, SourceEnum
from scraper.pipeline.alerter import build_email_html, send_digest


def make_listing(**overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        source=SourceEnum.CRAIGSLIST,
        source_id="1",
        url="https://example.com/1",
        title="10 Acres in Sullivan County",
        price=5000000,
        acreage=10.0,
        price_per_acre=500000.0,
        address="123 Rd",
        city="Liberty",
        county="Sullivan",
        state="NY",
        zip_code="12754",
        image_urls=[],
        raw_data={},
        first_seen_at=now,
        last_seen_at=now,
        is_active=True,
        notified=False,
    )
    defaults.update(overrides)
    return Listing(**defaults)


def test_build_email_html_contains_listing():
    listings = [make_listing(title="Amazing 10 Acres")]
    html = build_email_html(listings)
    assert "Amazing 10 Acres" in html
    assert "$50,000" in html  # 5000000 cents = $50,000


def test_build_email_html_multiple_listings():
    listings = [make_listing(title="Lot A"), make_listing(title="Lot B")]
    html = build_email_html(listings)
    assert "Lot A" in html
    assert "Lot B" in html


@patch("scraper.pipeline.alerter.resend")
def test_send_digest_calls_resend(mock_resend):
    mock_resend.Emails.send.return_value = {"id": "123"}
    listings = [make_listing()]
    send_digest(listings, to_email="test@example.com", api_key="re_test")
    mock_resend.Emails.send.assert_called_once()
    call_args = mock_resend.Emails.send.call_args[0][0]
    assert call_args["to"] == ["test@example.com"]


@patch("scraper.pipeline.alerter.resend")
def test_send_digest_skips_when_no_listings(mock_resend):
    send_digest([], to_email="test@example.com", api_key="re_test")
    mock_resend.Emails.send.assert_not_called()
