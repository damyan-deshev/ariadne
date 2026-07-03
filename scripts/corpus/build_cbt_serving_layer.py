#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TOPICS: dict[str, dict[str, Any]] = {
    "cbt_foundations": {
        "label": "CBT foundations",
        "description": "core CBT model, treatment structure, sessions, automatic thoughts, and basic therapist skills",
        "keywords": [
            "cognitive behavior therapy",
            "cognitive behavioural therapy",
            "what is cbt",
            "automatic thought",
            "cognitive model",
            "session",
            "action plan",
            "homework",
            "socratic",
        ],
    },
    "case_formulation": {
        "label": "case formulation",
        "description": "case conceptualization, cognitive formulations, schemas, beliefs, maintenance cycles, and resilience/vulnerability maps",
        "keywords": [
            "case formulation",
            "case conceptualization",
            "conceptualization",
            "formulation",
            "core belief",
            "intermediate belief",
            "schema",
            "maintenance cycle",
            "resilience",
            "vulnerability",
        ],
    },
    "behavioral_experiments": {
        "label": "behavioral experiments",
        "description": "behavioral experiments, prediction testing, exposure, safety behaviors, and learning reviews",
        "keywords": [
            "behavioral experiment",
            "behavioural experiment",
            "experiment",
            "prediction",
            "exposure",
            "safety behavior",
            "safety behaviour",
            "learning circle",
            "test",
        ],
    },
    "behavior_change": {
        "label": "behavior change",
        "description": "avoidance, behavioral activation, rumination, procrastination, emotion-driven behavior, and skills practice",
        "keywords": [
            "behavior",
            "behaviour",
            "avoidance",
            "behavioral activation",
            "behavioural activation",
            "rumination",
            "procrastination",
            "skills",
            "exposure",
            "emotion",
        ],
    },
    "eating_disorders": {
        "label": "eating disorders",
        "description": "CBT for eating disorders, binge eating, dietary restraint, body image, weight/shape concerns, and relapse prevention",
        "keywords": [
            "eating disorder",
            "eating disorders",
            "bulimia",
            "anorexia",
            "binge",
            "dietary restraint",
            "body image",
            "weight",
            "shape",
        ],
    },
    "therapeutic_process": {
        "label": "therapeutic process",
        "description": "collaborative empiricism, therapeutic relationship, agendas, supervision, therapist reflection, and treatment planning",
        "keywords": [
            "collaborative",
            "collaboration",
            "therapeutic relationship",
            "agenda",
            "supervision",
            "therapist",
            "treatment plan",
            "relapse",
            "client",
        ],
    },
}

TOPIC_ORDER = list(TOPICS)
CBT_PRIMARY_DISCIPLINE = "cognitive_behavioral_therapy"
CBT_NEGATIVE_SCOPE = [
    "emergency or crisis response",
    "medication prescribing or medication changes",
    "formal diagnosis without clinical assessment",
    "substitution for licensed professional care",
]
KNOWN_BOOK_OVERRIDES: list[tuple[str, dict[str, Any]]] = [
    (
        "cognitive behavior therapy and eating disorders",
        {
            "title": "Cognitive Behavior Therapy and Eating Disorders",
            "publisher": "The Guilford Press",
            "year": 2008,
        },
    ),
    (
        "cognitive behavior therapy, third edition",
        {
            "title": "Cognitive Behavior Therapy, Third Edition: Basics and Beyond",
            "publisher": "Guilford Publications, Inc.",
            "year": 2020,
            "edition": "3",
        },
    ),
    (
        "collaborative case conceptualization",
        {
            "title": "Collaborative Case Conceptualization: Working Effectively with Clients in Cognitive-Behavioral Therapy",
            "publisher": "The Guilford Press",
            "year": 2008,
        },
    ),
    (
        "doing cbt",
        {
            "title": "Doing CBT: A Comprehensive Guide to Working with Behaviors, Thoughts, and Emotions",
            "publisher": "The Guilford Press",
            "year": 2024,
            "edition": "2",
        },
    ),
    (
        "oxford guide to behavioural experiments",
        {
            "title": "Oxford Guide to Behavioural Experiments in Cognitive Therapy",
            "publisher": "Oxford University Press",
        },
    ),
    (
        "the case formulation approach",
        {
            "title": "The Case Formulation Approach to Cognitive-Behavior Therapy",
            "publisher": "The Guilford Press",
        },
    ),
]
NOISE_HEADINGS = {
    "about the author",
    "about the authors",
    "acknowledgments",
    "acknowledgements",
    "also by",
    "appendix",
    "bibliography",
    "contents",
    "copyright",
    "dedication",
    "foreword",
    "index",
    "preface",
    "references",
    "title page",
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_space(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_text(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return normalize_space(text.replace("_", " "))


def split_source_parts(filename: str) -> list[str]:
    return [clean_text(part) for part in Path(filename).stem.split("--") if clean_text(part)]


def parse_source_metadata(filename: str) -> dict[str, Any]:
    parts = split_source_parts(filename)
    title = (clean_text(parts[0]) if parts else clean_text(Path(filename).stem)).strip(" ,")
    authors = ""
    publisher = ""
    edition = ""
    year = None
    isbn13 = ""

    if len(parts) > 1:
        authors = re.sub(r"^by\s+", "", parts[1], flags=re.IGNORECASE)
    for part in parts[2:]:
        year_match = re.search(r"\b(19\d{2}|20\d{2})(?:\d{4})?\b", part)
        looks_like_edition = bool(re.search(r"\b\d+(?:st|nd|rd|th)?\b", part, flags=re.IGNORECASE))
        if "isbn13" in part.lower():
            isbn13 = part
        elif year_match:
            year = int(year_match.group(1))
            if looks_like_edition:
                edition = re.sub(r"\b(19\d{2}|20\d{2})\d{0,4}\b", "", part).strip(" ,") or part
        elif looks_like_edition and not edition and not re.fullmatch(r"[a-f0-9]{16,}", part, flags=re.IGNORECASE):
            edition = part
        elif not publisher and not re.fullmatch(r"[a-f0-9]{16,}", part, flags=re.IGNORECASE):
            publisher = part
    return {
        "title": title,
        "authors": authors,
        "publisher": publisher,
        "edition": edition,
        "year": year,
        "isbn13": isbn13,
    }


def apply_known_book_overrides(metadata: dict[str, Any]) -> dict[str, Any]:
    title_key = metadata.get("title", "").lower()
    for needle, overrides in KNOWN_BOOK_OVERRIDES:
        if needle in title_key:
            merged = dict(metadata)
            for key, value in overrides.items():
                if value not in (None, ""):
                    merged[key] = value
            return merged
    return metadata


def clean_heading(text: str) -> str | None:
    value = clean_text(re.sub(r"^#+\s*", "", text))
    value = re.sub(r"^\d+(\.\d+)*\s+", "", value)
    value = re.sub(r"^(chapter|part|section)\s+\d+[:,.\s-]*", "", value, flags=re.IGNORECASE)
    value = normalize_space(value.strip(" -:|"))
    if not value or len(value) < 4 or len(value) > 140:
        return None
    lowered = value.lower()
    if lowered in NOISE_HEADINGS:
        return None
    if any(lowered.startswith(item) for item in NOISE_HEADINGS):
        return None
    return value


def headings_from_catalog(catalog: dict[str, Any], limit: int = 18) -> list[str]:
    headings: list[str] = []
    for item in catalog.get("headings") or []:
        text = clean_heading(str(item.get("text") or ""))
        if text:
            headings.append(text)
    seen = set()
    result = []
    for heading in headings:
        key = heading.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(heading)
        if len(result) >= limit:
            break
    return result


def sample_text(selected_dir: Path, max_chars: int = 60000) -> str:
    chunks: list[str] = []
    for name in ["plain.txt", "figure-descriptions.md"]:
        path = selected_dir / name
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="ignore")[:max_chars])
    return "\n".join(chunks)[: max_chars * 2]


def score_topics(title: str, headings: list[str], sample: str) -> tuple[list[str], dict[str, int]]:
    haystack = " ".join([title, " ".join(headings), sample[:80000]]).lower()
    scores: dict[str, int] = {}
    for topic, meta in TOPICS.items():
        score = 0
        for keyword in meta["keywords"]:
            count = haystack.count(keyword.lower())
            if count:
                score += count * (4 if " " in keyword else 1)
        scores[topic] = score
    if "eating disorder" in title.lower():
        scores["eating_disorders"] += 80
    if "behavioural experiment" in title.lower() or "behavioral experiment" in title.lower():
        scores["behavioral_experiments"] += 80
    if "case formulation" in title.lower() or "case conceptualization" in title.lower():
        scores["case_formulation"] += 80
    if "doing cbt" in title.lower():
        scores["behavior_change"] += 60
        scores["cbt_foundations"] += 30
    ranked = [topic for topic, value in sorted(scores.items(), key=lambda item: (-item[1], TOPIC_ORDER.index(item[0]))) if value > 0]
    if not ranked:
        ranked = ["cbt_foundations"]
    return ranked[:4], scores


def figure_stats(selected_dir: Path) -> dict[str, int]:
    figures = read_json(selected_dir / "figures.json", [])
    descriptions = read_json(selected_dir / "figure-descriptions.json", [])
    qc_flags = sum(1 for item in descriptions if item.get("qc_flags") or item.get("error"))
    return {
        "figure_count": len(figures),
        "figure_description_count": len(descriptions),
        "figure_qc_flag_count": qc_flags,
    }


def rel_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def infer_resource_type(title: str, topics: list[str]) -> str:
    lowered = title.lower()
    if "basics and beyond" in lowered:
        return "textbook"
    if "behavioral experiments" in lowered or "behavioural experiments" in lowered:
        return "manual"
    if "doing cbt" in lowered or "eating disorders" in lowered:
        return "manual"
    if "case formulation" in lowered or "case conceptualization" in lowered:
        return "reference"
    if "therapeutic_process" in topics or "behavior_change" in topics:
        return "manual"
    return "reference"


def infer_evidence_tier(resource_type: str) -> str:
    if resource_type == "manual":
        return "clinical_manual"
    if resource_type == "textbook":
        return "textbook"
    return "reference"


def infer_coverage_phrases(title: str, topics: list[str], headings: list[str]) -> list[str]:
    phrases: list[str] = [title]
    for topic in topics:
        meta = TOPICS[topic]
        phrases.append(meta["label"])
        phrases.extend(meta["keywords"][:8])
    phrases.extend(headings[:10])

    result: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        value = clean_text(str(phrase))
        key = value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        result.append(value)
        if len(result) >= 24:
            break
    return result


def build_what_this_is(
    title: str,
    source_meta: dict[str, Any],
    topics: list[str],
    resource_type: str,
) -> str:
    topic_text = ", ".join(TOPICS[topic]["label"] for topic in topics[:3])
    author_text = source_meta.get("authors") or "the listed authors"
    publisher_text = source_meta.get("publisher") or "the source publisher"
    return (
        f"{title} is a CBT {resource_type} by {author_text}, published by "
        f"{publisher_text}, covering {topic_text}."
    )


def normalize_record(manifest_path: Path, compiled_root: Path) -> dict[str, Any]:
    doc_dir = manifest_path.parent
    selected_dir = doc_dir / "selected"
    manifest = read_json(manifest_path, {})
    catalog = read_json(selected_dir / "catalog.json", {})
    source_path = Path(manifest.get("source", {}).get("path") or catalog.get("source_filename") or doc_dir.name)
    source_filename = source_path.name
    source_meta = apply_known_book_overrides(parse_source_metadata(source_filename))
    title = source_meta["title"] or clean_text(catalog.get("document_title") or doc_dir.name)
    headings = headings_from_catalog(catalog)
    sample = sample_text(selected_dir)
    topics, topic_scores = score_topics(title, headings, sample)
    fig_stats = figure_stats(selected_dir)
    page_count = catalog.get("page_count")
    table_count = catalog.get("table_count")
    selected = manifest.get("selected_artifacts") or {}
    resource_type = infer_resource_type(title, topics)
    evidence_tier = infer_evidence_tier(resource_type)
    coverage_phrases = infer_coverage_phrases(title, topics, headings)
    clean_toc = headings[:18]
    what_this_is = build_what_this_is(title, source_meta, topics, resource_type)
    review_flags: list[str] = []
    if fig_stats["figure_count"] != fig_stats["figure_description_count"]:
        review_flags.append("figure_description_count_mismatch")
    if fig_stats["figure_qc_flag_count"]:
        review_flags.append("figure_description_qc_flags")
    if not selected.get("retrieval_markdown") and not (selected_dir / "retrieval.md").exists():
        review_flags.append("missing_retrieval_markdown")
    if page_count and page_count < 60 and source_path.suffix.lower() != ".epub":
        review_flags.append("unexpectedly_short_pdf")
    return {
        "book_id": doc_dir.name,
        "domain": "cbt",
        "title": title,
        "authors": source_meta["authors"],
        "publisher": source_meta["publisher"],
        "authority_or_publisher": source_meta["publisher"],
        "edition": source_meta["edition"],
        "year": source_meta["year"],
        "isbn13": source_meta["isbn13"],
        "source_filename": source_filename,
        "source_paths": [source_filename] if source_filename else [],
        "document_dir": rel_path(doc_dir, compiled_root),
        "selected_dir": rel_path(selected_dir, compiled_root) if selected_dir.exists() else None,
        "manifest_path": rel_path(manifest_path, compiled_root),
        "raw_markdown_path": rel_path(selected_dir / "raw.md", compiled_root),
        "retrieval_markdown_path": rel_path(selected_dir / "retrieval.md", compiled_root),
        "plain_text_path": rel_path(selected_dir / "plain.txt", compiled_root),
        "figure_descriptions_path": rel_path(selected_dir / "figure-descriptions.md", compiled_root),
        "primary_discipline": CBT_PRIMARY_DISCIPLINE,
        "resource_type": resource_type,
        "evidence_tier": evidence_tier,
        "coverage_phrases": coverage_phrases,
        "negative_scope": CBT_NEGATIVE_SCOPE,
        "clean_toc": clean_toc,
        "what_this_is": what_this_is,
        "secondary_tags": [TOPICS[topic]["label"] for topic in topics],
        "quarantine_reason": None,
        "topics": topics,
        "topic_scores": topic_scores,
        "headings": headings,
        "page_count": page_count,
        "table_count": table_count,
        **fig_stats,
        "parse_status": "success" if selected_dir.exists() and (selected_dir / "retrieval.md").exists() else "failed",
        "review_flags": review_flags,
    }


def directory_line(record: dict[str, Any]) -> str:
    meta = []
    if record.get("year"):
        meta.append(str(record["year"]))
    if record.get("authors"):
        meta.append(record["authors"])
    meta_text = f" ({'; '.join(meta)})" if meta else ""
    topics = ", ".join(TOPICS[item]["label"] for item in record["topics"])
    return f"- [{record['title']}](books/{record['book_id']}.md){meta_text}: {topics}."


def topic_line(record: dict[str, Any]) -> str:
    meta = []
    if record.get("authors"):
        meta.append(record["authors"])
    if record.get("year"):
        meta.append(str(record["year"]))
    meta_text = f" ({'; '.join(meta)})" if meta else ""
    return f"- [{record['title']}](../books/{record['book_id']}.md){meta_text}"


def book_card(record: dict[str, Any]) -> str:
    lines = [
        f"# {record['title']}",
        "",
        "## Source",
        "",
        f"- Authors: {record.get('authors') or 'unknown'}",
        f"- Year: {record.get('year') or 'unknown'}",
        f"- Publisher/body: {record.get('publisher') or 'unknown'}",
        f"- Pages/sections: {record.get('page_count') or 'unknown'}",
        f"- Tables: {record.get('table_count') or 0}",
        f"- Figures: {record.get('figure_count') or 0}",
        f"- Vision descriptions: {record.get('figure_description_count') or 0}",
        f"- Retrieval markdown: `{record['retrieval_markdown_path']}`",
        f"- Raw markdown: `{record['raw_markdown_path']}`",
        "",
        "## Best For",
        "",
    ]
    for topic in record["topics"]:
        lines.append(f"- {TOPICS[topic]['label']}: {TOPICS[topic]['description']}")
    lines.extend(["", "## Representative Contents", ""])
    if record["headings"]:
        for heading in record["headings"][:14]:
            lines.append(f"- {heading}")
    else:
        lines.append("- No clean headings extracted.")
    lines.extend(["", "## Use Notes", ""])
    if record.get("review_flags"):
        lines.append(f"- Review flags: {', '.join(record['review_flags'])}")
    else:
        lines.append("- No serving review flags.")
    if record.get("figure_qc_flag_count"):
        lines.append("- Some figure descriptions still have QC flags; inspect `figure-descriptions.json` before relying on those figures.")
    else:
        lines.append("- Figure descriptions passed structural QC after manual review.")
    lines.append("")
    return "\n".join(lines)


def build_indexes(output_root: Path, records: list[dict[str, Any]]) -> None:
    usable = [record for record in records if record["parse_status"] == "success"]
    topic_counts = Counter(topic for record in usable for topic in record["topics"])
    lines = [
        "# Local Corpus Index",
        "",
        f"- cbt: {len(usable)} usable CBT books",
        f"  Topics: {', '.join(topic for topic in TOPIC_ORDER if topic_counts[topic])}",
        "",
    ]
    write_text(output_root / "domains" / "index.md", "\n".join(lines))

    lines = [
        "# CBT Local Index",
        "",
        "Use topic files first. Open book cards after shortlisting likely sources.",
        "",
    ]
    for topic in TOPIC_ORDER:
        if not topic_counts[topic]:
            continue
        noun = "source" if topic_counts[topic] == 1 else "sources"
        lines.append(f"- [{TOPICS[topic]['label']}](topics/{topic}.md): {topic_counts[topic]} {noun}; {TOPICS[topic]['description']}.")
    lines.append("")
    lines.extend(directory_line(record) for record in sorted(usable, key=lambda item: item["title"].lower()))
    lines.append("")
    write_text(output_root / "domains" / "cbt" / "index.md", "\n".join(lines))

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in usable:
        for topic in record["topics"]:
            grouped[topic].append(record)
    for topic, items in grouped.items():
        items.sort(key=lambda item: (-item["topic_scores"].get(topic, 0), item["title"].lower()))
        lines = [
            f"# {TOPICS[topic]['label']}",
            "",
            TOPICS[topic]["description"].capitalize() + ".",
            "",
        ]
        lines.extend(topic_line(record) for record in items)
        lines.append("")
        write_text(output_root / "domains" / "cbt" / "topics" / f"{topic}.md", "\n".join(lines))

    for record in usable:
        write_text(output_root / "domains" / "cbt" / "books" / f"{record['book_id']}.md", book_card(record))


def build_review_files(output_root: Path, records: list[dict[str, Any]]) -> None:
    review = [record for record in records if record.get("review_flags")]
    failures = [record for record in records if record.get("parse_status") != "success"]
    lines = [
        "# Serving Review Queue",
        "",
        "Items here are usable but worth manual review for tighter routing.",
        "",
    ]
    if review:
        for record in review:
            lines.append(f"- {record['title']}: {', '.join(record['review_flags'])}")
    else:
        lines.append("- None.")
    lines.append("")
    write_text(output_root / "serving-review-queue.md", "\n".join(lines))
    write_text(
        output_root / "domains" / "cbt" / "failures.md",
        "# Failed Or Quarantined Sources\n\n"
        + ("\n".join(f"- {record['title']}: {record['parse_status']}" for record in failures) if failures else "- None.")
        + "\n",
    )
    (output_root / "serving-failures.json").write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8")


def write_catalog(output_root: Path, records: list[dict[str, Any]]) -> None:
    with (output_root / "serving-catalog.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a CBT-specific Markdown serving layer for a compiled Docling corpus.")
    parser.add_argument("compiled_root", type=Path)
    parser.add_argument("--output-name", default="_serving")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    compiled_root = args.compiled_root.expanduser().resolve()
    output_root = compiled_root / args.output_name
    if args.clean and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    records = [
        normalize_record(path, compiled_root)
        for path in sorted(compiled_root.glob("*/manifest.json"))
    ]
    records.sort(key=lambda item: item["title"].lower())
    build_indexes(output_root, records)
    build_review_files(output_root, records)
    write_catalog(output_root, records)
    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "records": len(records),
                "usable_records": sum(1 for record in records if record["parse_status"] == "success"),
                "review_records": sum(1 for record in records if record.get("review_flags")),
                "catalog": str(output_root / "serving-catalog.jsonl"),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
