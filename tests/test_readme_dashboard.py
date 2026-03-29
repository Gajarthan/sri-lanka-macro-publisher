from __future__ import annotations

from macro_publisher.reports.readme_dashboard import (
    BEGIN_MARKER,
    END_MARKER,
    render_dashboard_markdown,
    replace_dashboard_block,
)


def test_replace_dashboard_block_only_changes_bounded_section() -> None:
    original = (
        "# Title\n\n"
        "before\n\n"
        f"{BEGIN_MARKER}\nold block\n{END_MARKER}\n\n"
        "after\n"
    )

    updated = replace_dashboard_block(original, "new block")

    assert updated == (
        "# Title\n\n"
        "before\n\n"
        f"{BEGIN_MARKER}\nnew block\n{END_MARKER}\n\n"
        "after\n"
    )


def test_render_dashboard_markdown_contains_required_sections() -> None:
    markdown = render_dashboard_markdown()

    assert "## Published Data Dashboard" in markdown
    assert "### Latest Snapshot" in markdown
    assert "### Inflation Summary" in markdown
    assert "### Source Health" in markdown
    assert "### Exchange Rates Sample" in markdown
    assert "### Vegetable Prices Sample" in markdown
    assert "### Dashboard-to-File Mapping" in markdown
    assert "### Freshness and Cadence" in markdown
    assert "Monthly DCS CCPI release" in markdown
