from scraper.pipeline.normalizer import parse_price, parse_acreage, detect_features


def test_parse_price_with_dollar_sign():
    assert parse_price("$45,000") == 4500000


def test_parse_price_plain_number():
    assert parse_price("45000") == 4500000


def test_parse_price_with_k_suffix():
    assert parse_price("$45K") == 4500000


def test_parse_price_none_on_invalid():
    assert parse_price("Call for price") is None


def test_parse_price_none_on_empty():
    assert parse_price("") is None


def test_parse_acreage_with_acres():
    assert parse_acreage("10 acres") == 10.0


def test_parse_acreage_decimal():
    assert parse_acreage("2.5 ac") == 2.5


def test_parse_acreage_plain_number():
    assert parse_acreage("15") == 15.0


def test_parse_acreage_none_on_invalid():
    assert parse_acreage("N/A") is None


def test_detect_features_water():
    features = detect_features("Beautiful property with well water and creek access")
    assert features["has_water"] is True


def test_detect_features_utilities():
    features = detect_features("Electric and gas available at the road")
    assert features["has_utilities"] is True


def test_detect_features_road():
    features = detect_features("Paved road frontage, easy access")
    assert features["has_road_access"] is True


def test_detect_features_none_when_missing():
    features = detect_features("Nice wooded lot, very private")
    assert features["has_water"] is None
    assert features["has_utilities"] is None
    assert features["has_road_access"] is None
