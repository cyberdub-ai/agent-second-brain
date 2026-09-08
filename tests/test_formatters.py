"""Tests for Telegram delivery formatters: splitting and truncation."""

from d_brain.bot.formatters import (
    format_process_report,
    MAX_RESPONSE_LENGTH,
    split_text,
    truncate_html,
)


class TestSplitText:
    def test_short_text_passes_through(self):
        assert split_text("hello", MAX_RESPONSE_LENGTH) == ["hello"]

    def test_chunks_respect_limit(self):
        text = "слово " * 2000  # ~12000 chars
        chunks = split_text(text, MAX_RESPONSE_LENGTH)
        assert len(chunks) > 1
        assert all(len(c) <= MAX_RESPONSE_LENGTH for c in chunks)

    def test_no_content_lost_when_tag_spans_boundary(self):
        # An open <b> at the cut point makes truncate_html append
        # "...</b>" — the split must still advance by the ORIGINAL
        # characters consumed, not by the decorated chunk length.
        payload = "x" * 9000
        text = f"<b>{payload}</b>"
        chunks = split_text(text, MAX_RESPONSE_LENGTH)
        joined = "".join(chunks)
        assert joined.count("x") == 9000

    def test_no_content_lost_or_duplicated_in_plain_text(self):
        # The ellipsis decoration is dots-only, so letter counts must
        # survive the split exactly (no loss, no duplication).
        text = "abc. " * 2000  # 10000 chars, sentences end with dots
        chunks = split_text(text, MAX_RESPONSE_LENGTH)
        joined = "".join(chunks)
        for letter in "abc":
            assert joined.count(letter) == 2000

    def test_progress_on_pathological_input(self):
        # Must terminate even when the cut point math degenerates.
        text = "." * 5000
        chunks = split_text(text, MAX_RESPONSE_LENGTH)
        assert all(len(c) <= MAX_RESPONSE_LENGTH for c in chunks)
        assert "".join(chunks).count(".") >= 5000


class TestTruncateHtml:
    def test_short_text_untouched(self):
        assert truncate_html("<b>hi</b>", 4096) == "<b>hi</b>"

    def test_closes_open_tags(self):
        text = "<b>" + "x" * 5000
        out = truncate_html(text, 4096)
        assert len(out) <= 4096
        assert out.endswith("</b>")


class TestProcessReportLimit:
    def test_broken_tags_fallback_respects_limit(self):
        # Unbalanced HTML sends format_process_report down the plain-text
        # branch — it must still fit into a single Telegram message.
        report = {"report": "<b>" + "я" * 9000}
        assert len(format_process_report(report)) <= MAX_RESPONSE_LENGTH

    def test_deeply_nested_tags_respect_limit(self):
        # Closing tags are appended AFTER the cut: a fixed reserve is not
        # enough when nesting is deep.
        text = "<b><i><u>" * 20 + "x" * 5000
        assert len(truncate_html(text, max_length=200)) <= 200
