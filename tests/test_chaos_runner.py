from chaos.run import find_firing_result


def test_firing_result_ignores_resolved_alerts_with_same_name():
    firing = {
        "alertname": "TargetDown",
        "status": "firing",
        "ticket_url": "http://localhost:8092/browse/MOCK-1",
    }
    results = [
        firing,
        {"alertname": "TargetDown", "status": "resolved", "ticket_url": ""},
    ]

    assert find_firing_result(results, "TargetDown") == firing


def test_firing_result_requires_expected_alert():
    results = [
        {
            "alertname": "ApiHighLatency",
            "status": "firing",
            "ticket_url": "http://localhost:8092/browse/MOCK-1",
        }
    ]

    assert find_firing_result(results, "TargetDown") == {}
