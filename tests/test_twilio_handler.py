"""Tests for Twilio voice webhook routing."""

import pytest

from src.telephony.twilio_handler import CallFormData, TwilioVoiceHandler


class _FormRequest:
    def __init__(self, data: dict[str, str]):
        self._data = data

    async def form(self):
        return self._data


@pytest.mark.asyncio
class TestTwilioVoiceHandler:
    async def test_inbound_returns_greeting_twiml(self):
        handler = TwilioVoiceHandler()
        request = _FormRequest({"CallSid": "CA1", "From": "+15551234567"})
        response = await handler.handle_inbound(request)
        body = response.body.decode()
        assert "<Gather" in body
        assert "Hello" in body or "help" in body.lower()

    async def test_process_invokes_agent_on_speech(self):
        handler = TwilioVoiceHandler()
        data = CallFormData(
            call_sid="CA2",
            from_number="+15551234567",
            speech_result="How do I reset my password?",
        )
        request = _FormRequest({
            "CallSid": data.call_sid,
            "From": data.from_number,
            "SpeechResult": data.speech_result,
        })
        response = await handler.handle_process(request, data)
        body = response.body.decode()
        assert "<Say" in body or "<Gather" in body

    async def test_process_without_speech_reprompts(self):
        handler = TwilioVoiceHandler()
        request = _FormRequest({"CallSid": "CA3", "From": "+15551234567"})
        response = await handler.handle_process(request)
        body = response.body.decode()
        assert "<Gather" in body

    async def test_simulate_routes_to_process_when_speech_provided(self):
        handler = TwilioVoiceHandler()
        twiml = await handler.simulate(
            call_sid="SIM-1",
            from_number="+15551234567",
            speech_result="I need a manager",
        )
        assert "<Dial" in twiml or "specialist" in twiml.lower() or "<Say" in twiml
