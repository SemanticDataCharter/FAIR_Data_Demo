"""
BRFSS HTML codebook parser.

Parses the SAS-generated HTML codebook for the BRFSS 2022 LLCP dataset.
Extracts per-variable: label, section name, question text, value labels.

The codebook HTML structure (per variable):
  - A <td class="linecontent"> cell with metadata fields separated by <br> tags:
    Label, Section Name, Section Number, Question Number, Column,
    Type of Variable, SAS Variable Name, Question Prologue, Question
  - A value table with columns: Value, Value Label, Frequency, Percentage, Weighted %
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

CODEBOOK_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "source_data" / "brfss"
    / "codebook22_llcp-v2-508" / "USCODE22_LLCP_102523.HTML"
)


@dataclass
class BRFSSColumnMeta:
    """Metadata for a single BRFSS variable."""
    label: str = ""
    section: str = ""
    question: str = ""
    question_prologue: str = ""
    value_labels: dict[str, str] = field(default_factory=dict)


def _clean_text(text: str) -> str:
    """Clean HTML entities and normalize whitespace."""
    text = text.replace("\xa0", " ").replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_metadata_cell(cell_text: str) -> dict[str, str]:
    """Parse a linecontent cell into key-value pairs.

    The cell contains fields like:
      Label: State FIPS Code
      Section Name: Record Identification
      SAS Variable Name: _STATE
      Question: State FIPS Code
    """
    result: dict[str, str] = {}
    # Split on <br> tags first, then clean
    parts = re.split(r"<br\s*/?>", cell_text)
    for part in parts:
        cleaned = _clean_text(part)
        # Remove HTML tags
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = cleaned.strip()
        if not cleaned:
            continue
        # Split on first colon
        if ":" in cleaned:
            key, _, value = cleaned.partition(":")
            result[key.strip()] = value.strip()
    return result


def load_brfss_metadata() -> dict[str, BRFSSColumnMeta]:
    """Parse the BRFSS HTML codebook and extract per-variable metadata.

    Returns:
        Dict mapping SAS variable name → BRFSSColumnMeta.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 required: pip install beautifulsoup4")
        return {}

    if not CODEBOOK_PATH.exists():
        logger.warning("BRFSS codebook not found: %s", CODEBOOK_PATH)
        return {}

    logger.info("Parsing BRFSS codebook: %s", CODEBOOK_PATH)

    with open(CODEBOOK_PATH, "r", encoding="windows-1252", errors="replace") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    result: dict[str, BRFSSColumnMeta] = {}

    # Find all tables with class "table" — each contains one variable
    tables = soup.find_all("table", class_="table")

    for table in tables:
        # Find the linecontent cell (metadata header)
        meta_cell = table.find("td", class_="linecontent")
        if not meta_cell:
            continue

        # Parse metadata from the cell's inner HTML
        cell_html = str(meta_cell)
        fields = _parse_metadata_cell(cell_html)

        var_name = fields.get("SAS Variable Name", "").strip()
        if not var_name:
            continue

        meta = BRFSSColumnMeta(
            label=fields.get("Label", ""),
            section=fields.get("Section Name", ""),
            question=fields.get("Question", ""),
            question_prologue=fields.get("Question Prologue", ""),
        )

        # Parse value labels from the data rows
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    value = _clean_text(cells[0].get_text())
                    label = _clean_text(cells[1].get_text())
                    if value and label and value.upper() != "BLANK":
                        # Strip routing instructions (e.g., "Yes→Go to LL.02")
                        # Keep just the meaningful part before the arrow
                        if "\u2192" in label:
                            label = label.split("\u2192")[0].strip()
                        elif "→" in label:
                            label = label.split("→")[0].strip()
                        # Also handle the Windows-1252 arrow character
                        if "\x97" in label:
                            label = label.split("\x97")[0].strip()
                        meta.value_labels[value] = label

        result[var_name] = meta

    logger.info("Parsed BRFSS metadata for %d variables", len(result))
    return result
