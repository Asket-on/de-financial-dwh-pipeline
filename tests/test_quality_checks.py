from src.extract import read_sources


def test_sample_sources_have_required_fields():
    transactions, currencies = read_sources()
    assert not transactions["operation_id"].isna().any()
    assert not transactions["amount"].isna().any()
    assert not currencies["currency_with_div"].isna().any()


def test_sample_amounts_are_non_negative():
    transactions, _ = read_sources()
    assert (transactions["amount"] >= 0).all()
