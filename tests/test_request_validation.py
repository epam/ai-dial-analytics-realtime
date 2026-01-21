from tests.utils.client import Client


def test_invalid_data_message(client: Client):
    response = client.post_json(
        [
            "invalid message",
            {"message": "invalid message JSON"},
            {"message": '["\n'},
        ],
    ).raise_for_status()

    assert response.json() == [
        {
            "status": "error",
            "error": """
1 validation error for Message
__root__
  Message expected dict not str (type=type_error)
""".strip(),
            "reason": "invalid request message",
        },
        {
            "status": "error",
            "error": "Expecting value: line 1 column 1 (char 0)",
            "reason": "invalid JSON in request message",
        },
        {
            "status": "error",
            "error": "Unterminated string starting at: line 1 column 2 (char 1)",
            "reason": "invalid JSON in request message",
        },
    ]


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
                "loc": ["body", "__root__"],
                "msg": "value is not a valid list",
                "type": "type_error.list",
            }
        ]
    }
