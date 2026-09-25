# ANGELA-MATRIX: L4 [α] [A] [L2]

from cli.repl import _response_text


def test_response_text_extracts_dict_text():
    assert _response_text({"text": "local answer", "backend": "knowledge"}) == "local answer"


def test_response_text_preserves_object_text():
    class Response:
        text = "llm answer"

    assert _response_text(Response()) == "llm answer"
