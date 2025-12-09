"""Tests for API schemas."""

import pytest
from pydantic import ValidationError

from src.api.schemas import ChatMessage, ChatCompletionRequest


class TestChatMessage:
    def test_valid_user_message(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_valid_assistant_message(self):
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"

    def test_valid_system_message(self):
        msg = ChatMessage(role="system", content="You are helpful.")
        assert msg.role == "system"

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid", content="test")

    def test_empty_content_allowed(self):
        msg = ChatMessage(role="user", content="")
        assert msg.content == ""


class TestChatCompletionRequest:
    def test_valid_request_minimal(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")]
        )
        assert len(request.messages) == 1
        assert request.max_tokens == 2048
        assert request.temperature == 0.7
        assert request.stream is False

    def test_valid_request_all_fields(self):
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="system", content="Be helpful"),
                ChatMessage(role="user", content="Hi")
            ],
            model="test-model",
            max_tokens=500,
            temperature=0.5,
            top_p=0.9,
            stream=True,
            stop=["\n"]
        )
        assert len(request.messages) == 2
        assert request.model == "test-model"
        assert request.max_tokens == 500

    def test_empty_messages_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatCompletionRequest(messages=[])
        assert "min_length" in str(exc_info.value) or "at least" in str(exc_info.value).lower()

    def test_temperature_lower_bound(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hi")],
            temperature=0.0
        )
        assert request.temperature == 0.0

    def test_temperature_upper_bound(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hi")],
            temperature=2.0
        )
        assert request.temperature == 2.0

    def test_temperature_below_range_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                temperature=-0.1
            )

    def test_temperature_above_range_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                temperature=2.1
            )

    def test_max_tokens_valid_range(self):
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hi")],
            max_tokens=1
        )
        assert request.max_tokens == 1

    def test_max_tokens_zero_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                max_tokens=0
            )

    def test_max_tokens_negative_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="Hi")],
                max_tokens=-1
            )
