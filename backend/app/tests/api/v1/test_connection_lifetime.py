from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings


def _experiment_url(path: str) -> str:
    return f"{settings.API_V1_STR}/experiments/connection-lifetime{path}"


def test_filters_variants_align(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    expected = client.get(
        _experiment_url("/filters-di"), headers=superuser_token_headers
    )
    assert expected.status_code == 200
    baseline_payload = expected.json()

    inline = client.get(
        _experiment_url("/filters-inline"), headers=superuser_token_headers
    )
    assert inline.status_code == 200
    assert inline.json() == baseline_payload

    di_noquery = client.get(
        _experiment_url("/filters-di-noquery"),
        headers=superuser_token_headers,
    )
    assert di_noquery.status_code == 200
    assert di_noquery.json() == baseline_payload

    inline_mw = client.get(
        _experiment_url("/filters-inline-mw"), headers=superuser_token_headers
    )
    assert inline_mw.status_code == 200
    assert inline_mw.json() == baseline_payload


def test_pool_metrics_surface_checkout_counts(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    initial = client.get(f"{settings.API_V1_STR}/_pool")
    assert initial.status_code == 200
    payload_before = initial.json()
    assert payload_before["available"] is True

    client.get(_experiment_url("/filters-di"), headers=superuser_token_headers)
    client.get(_experiment_url("/filters-inline"), headers=superuser_token_headers)

    after = client.get(f"{settings.API_V1_STR}/_pool")
    assert after.status_code == 200
    payload_after = after.json()
    assert payload_after["available"] is True
    assert payload_after["total_checkouts"] >= payload_before["total_checkouts"] + 2
    assert "checked_out_now" in payload_after
    assert isinstance(payload_after["in_flight_holds"], list)
