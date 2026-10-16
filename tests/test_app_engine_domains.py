"""Phase 4: domain-aware default entities for prompt-only app shells."""
import pytest
from backend.engines import app_engine


@pytest.mark.parametrize("brief,names", [
    ("CRM for customers and deals", ["Customer", "Deal"]),
    ("booking app for salons", ["Booking"]),
    ("warehouse inventory system", ["Item"]),
    ("invoice generator", ["Invoice"]),
    ("todo app", ["Task"]),
    ("notes app with tags", ["Note"]),
])
def test_default_entities_follow_domain(brief, names):
    assert [e["name"] for e in app_engine._default_entities("management", brief)] == names


def test_entity_fields_use_supported_types():
    ok = {"string", "text", "int", "float", "bool", "datetime", "email", "url", "enum", "ref"}
    for brief in ("CRM", "booking", "inventory", "invoice"):
        for e in app_engine._default_entities("management", brief):
            assert all(f["type"] in ok for f in e["fields"])
