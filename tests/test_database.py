"""Unit tests for Database — all run against a temp SQLite file."""
import pytest


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

def test_tables_created(tmp_db):
    cursor = tmp_db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert 'conversations' in tables
    assert 'messages' in tables


# ---------------------------------------------------------------------------
# create_conversation
# ---------------------------------------------------------------------------

def test_create_conversation_returns_id(tmp_db):
    conv_id = tmp_db.create_conversation("B2", "Technology")
    assert isinstance(conv_id, int)
    assert conv_id >= 1


def test_create_conversation_persists_level_and_subject(tmp_db):
    conv_id = tmp_db.create_conversation("A1", "Greetings")
    row = tmp_db.get_conversation(conv_id)
    assert row[1] == "A1"
    assert row[2] == "Greetings"


def test_multiple_conversations_have_distinct_ids(tmp_db):
    id1 = tmp_db.create_conversation("A1", "Food")
    id2 = tmp_db.create_conversation("B1", "Work")
    assert id1 != id2


# ---------------------------------------------------------------------------
# add_message / get_messages
# ---------------------------------------------------------------------------

def test_add_user_message(tmp_db):
    conv_id = tmp_db.create_conversation("B1", "Work")
    tmp_db.add_message(conv_id, "Hello!", "user")
    msgs = tmp_db.get_messages(conv_id)
    assert len(msgs) == 1
    assert msgs[0] == ("Hello!", "user")


def test_add_ai_message(tmp_db):
    conv_id = tmp_db.create_conversation("B1", "Work")
    tmp_db.add_message(conv_id, "Hi there!", "ai")
    msgs = tmp_db.get_messages(conv_id)
    assert msgs[0] == ("Hi there!", "ai")


def test_messages_returned_in_chronological_order(tmp_db):
    conv_id = tmp_db.create_conversation("A2", "Travel")
    tmp_db.add_message(conv_id, "First", "user")
    tmp_db.add_message(conv_id, "Second", "ai")
    tmp_db.add_message(conv_id, "Third", "user")
    texts = [m[0] for m in tmp_db.get_messages(conv_id)]
    assert texts == ["First", "Second", "Third"]


def test_add_message_updates_last_message(tmp_db):
    conv_id = tmp_db.create_conversation("C1", "Philosophy")
    tmp_db.add_message(conv_id, "Deep thought", "user")
    row = tmp_db.get_conversation(conv_id)
    assert row[3] == "Deep thought"  # last_message column


# ---------------------------------------------------------------------------
# get_conversations
# ---------------------------------------------------------------------------

def test_get_conversations_excludes_archived(tmp_db):
    active_id = tmp_db.create_conversation("A1", "Greetings")
    archived_id = tmp_db.create_conversation("B2", "Business")
    tmp_db.archive_conversation(archived_id, archived=True)

    active = [row[0] for row in tmp_db.get_conversations(archived=False)]
    assert active_id in active
    assert archived_id not in active


def test_get_conversations_archived_only(tmp_db):
    active_id = tmp_db.create_conversation("A1", "Greetings")
    archived_id = tmp_db.create_conversation("B2", "Business")
    tmp_db.archive_conversation(archived_id, archived=True)

    archived = [row[0] for row in tmp_db.get_conversations(archived=True)]
    assert archived_id in archived
    assert active_id not in archived


# ---------------------------------------------------------------------------
# archive / unarchive
# ---------------------------------------------------------------------------

def test_unarchive_conversation(tmp_db):
    conv_id = tmp_db.create_conversation("A2", "Shopping")
    tmp_db.archive_conversation(conv_id, archived=True)
    tmp_db.archive_conversation(conv_id, archived=False)

    active_ids = [row[0] for row in tmp_db.get_conversations(archived=False)]
    assert conv_id in active_ids


# ---------------------------------------------------------------------------
# update_note
# ---------------------------------------------------------------------------

def test_update_note(tmp_db):
    conv_id = tmp_db.create_conversation("C2", "Literature")
    tmp_db.update_note(conv_id, "Great session!")
    row = tmp_db.get_conversation(conv_id)
    assert row[6] == "Great session!"  # note column


# ---------------------------------------------------------------------------
# delete_conversation
# ---------------------------------------------------------------------------

def test_delete_conversation_removes_row(tmp_db):
    conv_id = tmp_db.create_conversation("B1", "Health")
    tmp_db.delete_conversation(conv_id)
    assert tmp_db.get_conversation(conv_id) is None


def test_delete_conversation_removes_its_messages(tmp_db):
    conv_id = tmp_db.create_conversation("B1", "Health")
    tmp_db.add_message(conv_id, "msg", "user")
    tmp_db.delete_conversation(conv_id)
    assert tmp_db.get_messages(conv_id) == []
