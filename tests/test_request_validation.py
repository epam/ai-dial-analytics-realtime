from tests.utils.client import Client


def test_invalid_data_message(client: Client):
    response = client.post_json(
        [
            "invalid message",
            {"message": "invalid message JSON"},
            {"message": '["\n'},
        ],
    ).raise_for_status()

    response_json = response.json()

    assert response_json[0]["status"] == "error"
    assert response_json[0]["reason"] == "invalid request message"
    assert "1 validation error for Message" in response_json[0]["error"]
    assert (
        "Input should be a valid dictionary or instance of Message"
        in response_json[0]["error"]
    )

    assert response_json[1] == {
        "status": "error",
        "error": "Expecting value: line 1 column 1 (char 0)",
        "reason": "invalid JSON in request message",
    }
    assert response_json[2] == {
        "status": "error",
        "error": "Unterminated string starting at: line 1 column 2 (char 1)",
        "reason": "invalid JSON in request message",
    }


def test_invalid_data_request_json(client: Client):
    response = client.http_client.post(
        "/data",
        content="invalid json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "json_invalid",
                "loc": ["body", 0],
                "msg": "JSON decode error",
                "input": {},
                "ctx": {"error": "Expecting value"},
            }
        ]
    }


def test_invalid_data_request_type(client: Client):
    response = client.post_json({"foo": "bar"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "list_type",
                "loc": ["body"],
                "msg": "Input should be a valid list",
                "input": {"foo": "bar"},
            }
        ]
    }
