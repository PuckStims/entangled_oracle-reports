from app.web import create_app


def test_review_edit_route_preserves_location_service_values():
    app = create_app()

    with app.test_client() as client:
        response = client.post(
            "/create/local_compass/edit",
            data={
                "name": "Aster",
                "birth_date": "1990-01-01",
                "birth_time": "12:00",
                "location": "Chicago, IL",
                "anchor_location": "Chicago, IL",
                "destination": "Milwaukee, WI",
                "purpose_lens": "study",
                "relationship_to_place": "",
                "report_date": "",
                "report_end_date": "",
                "route_waypoints": "41.8781,-87.6298;42.3314,-87.8601",
                "route_corridor_km": "120",
                "route_id": "chi-mke",
                "palette": "vibrant",
                "content_pack": "plainspeak",
                "consent_acknowledged": "yes",
            },
        )

    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'value="Aster"' in body
    assert 'value="Chicago, IL"' in body
    assert 'value="Milwaukee, WI"' in body
    assert 'value="study" selected' in body
    assert '41.8781,-87.6298;42.3314,-87.8601' in body
    assert 'value="chi-mke"' in body
