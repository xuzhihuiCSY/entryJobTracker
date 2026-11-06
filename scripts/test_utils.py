from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import requests

from utils import http_get_json, read_json, write_json


def response(status: int) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = b'{"ok":true}'
    return result


def test_transient_requests_retry_and_denials_do_not() -> None:
    with patch("utils.requests.get", side_effect=[requests.Timeout(), response(503), response(200)]) as get, patch("utils.time.sleep"):
        assert http_get_json("https://jobs.example.com/api")["ok"]
        assert get.call_count == 3
    for status in (401, 403, 404, 429):
        with patch("utils.requests.get", return_value=response(status)) as get, patch("utils.time.sleep"):
            try:
                http_get_json("https://jobs.example.com/api")
            except requests.HTTPError:
                pass
            else:
                raise AssertionError("Expected HTTP failure")
            assert get.call_count == 1


def test_atomic_json_write_leaves_only_complete_output() -> None:
    with TemporaryDirectory() as directory:
        target = Path(directory) / "snapshot.json"
        write_json(target, {"jobs": [1, 2]})
        write_json(target, {"jobs": []})
        assert read_json(target, None) == {"jobs": []}
        assert list(Path(directory).iterdir()) == [target]


if __name__ == "__main__":
    test_transient_requests_retry_and_denials_do_not()
    test_atomic_json_write_leaves_only_complete_output()
    print("request and atomic-write tests passed")
