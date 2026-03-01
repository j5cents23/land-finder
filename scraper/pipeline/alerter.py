import resend

from scraper.models import Listing


def _format_price(cents: int) -> str:
    return f"${cents // 100:,}"


def build_email_html(listings: list[Listing]) -> str:
    rows = []
    for listing in listings:
        rows.append(f"""
        <tr>
            <td><a href="{listing.url}">{listing.title}</a></td>
            <td>{_format_price(listing.price)}</td>
            <td>{listing.acreage:.1f} ac</td>
            <td>{_format_price(int(listing.price_per_acre))}/ac</td>
            <td>{listing.county}, {listing.state}</td>
            <td>{listing.source.value}</td>
        </tr>""")

    return f"""
    <html>
    <body>
        <h2>Land Finder: {len(listings)} New Match{"es" if len(listings) != 1 else ""}</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
            <tr>
                <th>Title</th><th>Price</th><th>Acreage</th>
                <th>Price/Acre</th><th>Location</th><th>Source</th>
            </tr>
            {"".join(rows)}
        </table>
    </body>
    </html>
    """


def send_digest(
    listings: list[Listing],
    to_email: str,
    api_key: str,
) -> None:
    if not listings:
        return

    resend.api_key = api_key
    html = build_email_html(listings)
    resend.Emails.send({
        "from": "Land Finder <landfinder@resend.dev>",
        "to": [to_email],
        "subject": f"Land Finder: {len(listings)} new listing{'s' if len(listings) != 1 else ''}",
        "html": html,
    })
