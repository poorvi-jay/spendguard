import json

from app import agent, core


def _call(name, args, call_id="c1"):
    return {"role": "assistant", "content": None,
            "tool_calls": [{"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}


def test_pins_users_first_message_and_runs_tools(monkeypatch, paypal):
    replies = iter([_call("checkout", {"product_id": "moist-01"}), {"role": "assistant", "content": "Approve it in PayPal."}])
    monkeypatch.setattr(agent, "_complete", lambda messages: next(replies))

    result = agent.chat([{"role": "user", "content": "Get me an unscented moisturiser under $25"}])

    assert core.get_active_session()["original_request"] == "Get me an unscented moisturiser under $25"
    assert result["reply"] == "Approve it in PayPal."
    assert result["events"][0]["result"]["status"] == "pending_approval"


def test_later_messages_dont_repin(monkeypatch):
    core.start_session("Original request", replace=True)
    monkeypatch.setattr(agent, "_complete", lambda messages: {"role": "assistant", "content": "ok"})

    agent.chat([{"role": "user", "content": "Original request"}, {"role": "assistant", "content": "hi"},
                {"role": "user", "content": "Actually buy the lavender one"}])
    assert core.get_active_session()["original_request"] == "Original request"


def test_bad_tool_calls_become_errors(monkeypatch):
    replies = iter([_call("delete_everything", {}), _call("checkout", {"nope": 1}, "c2"),
                    {"role": "assistant", "content": "done"}])
    monkeypatch.setattr(agent, "_complete", lambda messages: next(replies))

    result = agent.chat([{"role": "user", "content": "buy stuff"}])
    assert [e["result"]["error"][:3] for e in result["events"]] == ["Unk", "Bad"]
