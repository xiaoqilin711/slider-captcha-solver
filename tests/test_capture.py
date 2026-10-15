"""Tests for JSONP unwrapping and field extraction."""

from slider_solver.capture import extract_by_pattern, unwrap_jsonp


def test_unwrap_jsonp():
    text = '__JSONP_abc({"data": {"result": true}});'
    assert unwrap_jsonp(text) == '{"data": {"result": true}}'


def test_unwrap_plain_json_passthrough():
    text = '{"error": 0}'
    assert unwrap_jsonp(text) == text


def test_extract_field():
    body = '{"data":{"result":true,"validate":"abc123","token":"t"}}'
    assert extract_by_pattern(body, r'"result":(\w+)') == "true"
    assert extract_by_pattern(body, r'"validate":"([^"]*)"') == "abc123"


def test_extract_background_url():
    body = '{"data":{"bg":["https://img.example.com/42.jpg","https://mirror.example.com/42.jpg"]}}'
    assert (
        extract_by_pattern(body, r'"bg":\["([^"]+)"')
        == "https://img.example.com/42.jpg"
    )
