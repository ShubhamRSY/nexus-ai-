"""Tests for prompt message extraction."""

from langchain_core.messages import HumanMessage, SystemMessage

from src.prompts.templates import CHAT_PROMPT, messages_from_prompt_value


class TestPromptMessages:
    def test_messages_from_chat_prompt_value(self):
        formatted = CHAT_PROMPT.invoke({
            "agent_name": "Test Agent",
            "context": "KB context",
            "customer_info": "none",
            "conversation_summary": "N/A",
            "few_shot_block": "",
            "chain_of_thought_block": "",
            "input": "Hello",
            "chat_history": [],
        })
        messages = messages_from_prompt_value(formatted)
        assert len(messages) >= 2
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[-1], HumanMessage)
        assert messages[-1].content == "Hello"

    def test_messages_from_list_passthrough(self):
        msgs = [SystemMessage(content="sys"), HumanMessage(content="hi")]
        assert messages_from_prompt_value(msgs) == msgs
