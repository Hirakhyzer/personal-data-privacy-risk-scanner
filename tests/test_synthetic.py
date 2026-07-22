from privacyrisk.synthetic import SyntheticPrivacyConfig, generate_synthetic_privacy_data


def test_synthetic_data_shapes_and_keys():
    data = generate_synthetic_privacy_data(SyntheticPrivacyConfig(documents=24, seed=3))
    assert set(data) == {"documents", "access_log"}
    assert len(data["documents"]) == 24
    assert data["documents"]["document_id"].is_unique
    assert len(data["access_log"]) >= 40


def test_invalid_document_count_rejected():
    try:
        SyntheticPrivacyConfig(documents=5)
    except ValueError:
        assert True
    else:
        raise AssertionError("invalid config should fail")
