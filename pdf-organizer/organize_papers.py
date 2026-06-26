#!/usr/bin/env python3
"""
organize_papers.py — PDF Article Organizer (heuristics-based, no API required)

Classifies PDFs in ~/Downloads as journal articles or not using rule-based
heuristics (DOI detection, section headers, PDF metadata), extracts first-author
and year, renames to `firstauthor-year.pdf`, moves to ~/Documents/Work/Articles/,
applies Finder tags, and logs everything.

Usage:
    # Dry run first (always safe)
    python organize_papers.py --dry-run --limit 20 --verbose

    # Full run
    python organize_papers.py
"""

import argparse
import csv
import plistlib
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

try:
    import pypdf
except ImportError:
    sys.exit("pypdf not found. Run: pip install pypdf")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNOWN_TAGS = {
    "IDP": "2",
    "LLPS": "2",
    "Peptides": "2",
    "Metals": "2",
    "Cyclic": "2",
    "NMR": "3",
    "FRET": "3",
    "Evolution": "3",
    "Mechanics": "3",
    "Allostery": "4",
    "Binding": "4",
    "Bioinformatics": "4",
    "Ensembles": "4",
    "Entropy": "4",
    "Enzymes": "4",
    "Heme": "4",
    "Hydrogenase": "4",
    "Interactions": "4",
    "Polymer": "4",
    "QM": "4",
    "Thermodynamics": "4",
    "Water": "4",
    "CoarseGrained": "5",
    "Design": "5",
    "ForceFields": "5",
    "FreeEnergy": "5",
    "Kinetics": "5",
    "ML": "5",
    "MSM": "5",
    "Simulation": "5",
    "COVID19": "6",
    "DNA/RNA": "6",
    "Aggregation": "7",
    "Folding": "7",
    "Mutation": "7",
    "Structure": "7",
    "TP/Friction": "7",
    "Downhill": "1",
    "Smfs": "0",
}

# Keywords for tag assignment. Checked against title + abstract text (case-insensitive).
TAG_KEYWORDS = {
    "IDP": [
        "intrinsically disordered", "intrinsically unstructured", "idp", "idr",
        "disordered protein", "disordered region", "unfolded protein", "natively unfolded",
    ],
    "LLPS": [
        "liquid-liquid phase separation", "llps", "phase separation", "condensate",
        "biomolecular condensate", "membraneless organelle", "coacervate",
    ],
    "Peptides": [
        "peptide", "dipeptide", "tripeptide", "oligopeptide", "cyclic peptide",
        "antimicrobial peptide", "amp",
    ],
    "Metals": [
        "metal ion", "metalloprotein", "zinc", "copper", "iron", "calcium",
        "magnesium", "manganese", "cobalt", "nickel", "metalloenzyme",
    ],
    "Cyclic": [
        "cyclic peptide", "cyclization", "cyclic dinucleotide",
    ],
    "NMR": [
        " nmr ", "nuclear magnetic resonance", "chemical shift", "relaxation dispersion",
        "noe ", "noesy", "hsqc", "residual dipolar coupling", "rdc",
    ],
    "FRET": [
        "fret", "förster resonance", "forster resonance", "single-molecule fret",
        "smfret", "fluorescence resonance",
    ],
    "Evolution": [
        "evolution", "evolutionary", "phylogenetic", "natural selection",
        "conservation", "sequence conservation", "homolog",
    ],
    "Mechanics": [
        "atomic force microscopy", "afm", "mechanical unfolding", "force spectroscopy",
        "stretching", "elasticity", "mechanical stability", "optical tweezer",
    ],
    "Allostery": [
        "allostery", "allosteric", "conformational change", "effector",
    ],
    "Binding": [
        "binding affinity", "dissociation constant", "kd ", "kon ", "koff",
        "protein-protein interaction", "ligand binding", "docking",
    ],
    "Bioinformatics": [
        "bioinformatics", "sequence alignment", "database", "genome", "proteome",
        "blast", "hmm", "sequence analysis", "deep learning", "neural network",
    ],
    "Ensembles": [
        "conformational ensemble", "structural ensemble", "ensemble",
        "population", "heterogeneous", "conformational sampling",
    ],
    "Entropy": [
        "entropy", "entropic", "free energy landscape", "thermodynamic",
        "configurational entropy",
    ],
    "Enzymes": [
        "enzyme", "catalysis", "catalytic", "substrate", "active site",
        "michaelis", "turnover", "enzymatic",
    ],
    "Heme": [
        "heme", "haeme", "cytochrome", "hemoglobin", "myoglobin", "porphyrin",
    ],
    "Hydrogenase": [
        "hydrogenase", "hydrogen evolution", "h2 production",
    ],
    "Interactions": [
        "protein interaction", "molecular interaction", "electrostatic",
        "van der waals", "hydrophobic interaction",
    ],
    "Polymer": [
        "polymer", "polyelectrolyte", "polymer physics", "worm-like chain",
        "freely jointed chain", "persistence length",
    ],
    "QM": [
        "quantum mechanics", "qm/mm", "density functional", "dft",
        "ab initio", "quantum chemical", "hartree-fock",
    ],
    "Thermodynamics": [
        "thermodynamics", "enthalpy", "heat capacity", "calorimetry",
        "differential scanning", "isothermal titration",
    ],
    "Water": [
        "water molecule", "hydration", "solvation", "water dynamics",
        "hydrophobic effect", "water network",
    ],
    "CoarseGrained": [
        "coarse-grained", "coarse grained", "cg model", "martini",
        "go model", "go-like", "elastic network",
    ],
    "Design": [
        "protein design", "de novo design", "computational design",
        "directed evolution", "engineering",
    ],
    "ForceFields": [
        "force field", "amber ff", "charmm36", "opls", "gromos",
        "force-field", "parameterization", "forcefield",
    ],
    "FreeEnergy": [
        "free energy", "potential of mean force", "pmf", "umbrella sampling",
        "free energy perturbation", "fep", "thermodynamic integration",
        "metadynamics", "replica exchange",
    ],
    "Kinetics": [
        "kinetics", "rate constant", "rate coefficient", "folding rate",
        "unfolding rate", "transition state", "kramers", "diffusion",
    ],
    "ML": [
        "machine learning", "deep learning", "neural network", "alphafold",
        "transformer", "graph neural", "random forest", "support vector",
    ],
    "MSM": [
        "markov state model", "msm", "transition network", "kinetic network",
        "committor", "metzner",
    ],
    "Simulation": [
        "molecular dynamics", "monte carlo simulation", "md simulation",
        "amber", "gromacs", "namd", "openmm", "charmm",
        "trajectory", "force field",
    ],
    "COVID19": [
        "covid", "sars-cov", "coronavirus", "spike protein", "ace2",
        "pandemic", "viral",
    ],
    "DNA/RNA": [
        "dna", "rna", "nucleic acid", "nucleotide", "base pair",
        "double helix", "ribosome", "transcript",
    ],
    "Aggregation": [
        "aggregation", "amyloid", "fibril", "prion", "misfolding",
        "inclusion body", "oligomer",
    ],
    "Folding": [
        "protein folding", "unfolding", "refolding", "folding pathway",
        "chaperone", "denaturation", "two-state", "folding kinetics",
    ],
    "Mutation": [
        "mutation", "mutant", "point mutation", "substitution",
        "single nucleotide polymorphism", "snp", "variant",
    ],
    "Structure": [
        "crystal structure", "x-ray crystallography", "cryo-em", "cryoem",
        "structure determination", "pdb", "secondary structure",
        "tertiary structure", "quaternary",
    ],
    "TP/Friction": [
        "transition path", "friction", "recrossing", "diffusion coefficient",
        "memory kernel", "generalized langevin",
    ],
    "Downhill": [
        "downhill folding", "barrierless folding", "one-state folding",
        "type 0 folding",
    ],
    "Smfs": [
        "single molecule", "single-molecule", "smfs", "optical trap",
        "magnetic tweezer",
    ],
}

# Patterns that strongly suggest a non-article document
NON_ARTICLE_PATTERNS = [
    r"\binvoice\b",
    r"\breceipt\b",
    r"\border\s+confirmation\b",
    r"\bpurchase\s+order\b",
    r"\btax\s+invoice\b",
    r"\bstatement\s+of\s+account\b",
    r"\bpayment\s+due\b",
    r"\bamount\s+due\b",
    r"\bvat\s+number\b",
    r"\bcurriculum\s+vitae\b",
    r"\bresume\b",
    r"\bcover\s+letter\b",
    r"\bboard\s+of\s+directors\b",
    r"\bslide\s+\d+\b",           # presentation slides
    r"\blecture\s+notes?\b",
    r"\bchapter\s+\d+\b",         # thesis/book chapters
    r"\bthesis\b",
    r"\bdissertation\b",
    r"\btable\s+of\s+contents\b",
    r"\bindex\b.*\bpage\b",
]

# Known journal name fragments (not exhaustive but covers common ones)
JOURNAL_PATTERNS = [
    r"nature\s+(communications|chemistry|physics|methods|structural|chemical)",
    r"journal\s+of\s+(the\s+)?",
    r"physical\s+review\s+letters?",
    r"proc\.?\s+natl\.?\s+acad\.?\s+sci",
    r"pnas\b",
    r"j\.?\s+chem\.?\s+phys",
    r"j\.?\s+am\.?\s+chem\.?\s+soc",
    r"jacs\b",
    r"biophys\.?\s+j",
    r"proteins?:",
    r"biochemistry\b",
    r"angew\.?\s+chem",
    r"chemphyschem",
    r"plos\s+(one|comput|biol)",
    r"elife\b",
    r"science\b",
    r"cell\b",
    r"\bpeerj\b",
    r"scientific\s+reports",
    r"nucleic\s+acids",
    r"structure\b",
    r"curr\.?\s+opin",
    r"annu\.?\s+rev",
    r"chem\.?\s+rev",
    r"accounts\s+of\s+chem",
    r"biopolymers\b",
    r"protein\s+sci",
    r"j\.?\s+mol\.?\s+biol",
    r"j\.?\s+phys\.?\s+chem",
    r"langmuir\b",
    r"soft\s+matter",
    r"macromolecules\b",
    r"acs\s+(nano|cent|catal)",
    r"nanoscale\b",
]

DEFAULT_DOWNLOADS = Path.home() / "Downloads"
DEFAULT_ARTICLES = Path.home() / "Documents" / "Work" / "Articles"
DEFAULT_LOG = Path.home() / "Downloads" / "organize_papers.csv"

CSV_FIELDS = [
    "source_path",
    "dest_path",
    "original_filename",
    "new_filename",
    "author",
    "year",
    "tags",
    "is_article",
    "confidence",
    "action",
    "error",
]


# ---------------------------------------------------------------------------
# Text and metadata extraction
# ---------------------------------------------------------------------------

def extract_pdf_info(pdf_path: Path) -> tuple[str, dict]:
    """
    Returns (text, metadata) where text is from pages 0-1 (capped at 4000 chars)
    and metadata is the PDF /Info dict.
    """
    text = ""
    metadata = {}
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        meta = reader.metadata or {}
        metadata = {str(k).lstrip("/"): str(v) for k, v in meta.items() if v}
        for page in reader.pages[:2]:
            text += page.extract_text() or ""
        text = text[:4000]
    except Exception:
        pass

    if len(text.strip()) < 50:
        # Fallback: ghostscript
        try:
            result = subprocess.run(
                ["gs", "-sDEVICE=txtwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
                 "-sOutputFile=-", "-dLastPage=2", str(pdf_path)],
                capture_output=True, text=True, timeout=30,
            )
            text = result.stdout[:4000]
        except Exception:
            pass

    return text, metadata


# ---------------------------------------------------------------------------
# Heuristic classification
# ---------------------------------------------------------------------------

def classify(text: str, metadata: dict) -> dict:
    """
    Returns dict with keys: is_article, author, year, tags, confidence, reason.
    Uses only heuristics — no external API.
    """
    text_lower = text.lower()
    combined = (metadata.get("Title", "") + " " + text).lower()

    # --- Non-article veto ---
    for pattern in NON_ARTICLE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return {
                "is_article": False,
                "reason": f"non-article pattern: {pattern}",
                "author": "", "year": "", "tags": [], "confidence": "high",
            }

    # --- Positive signals ---
    score = 0
    signals = []

    # DOI is the strongest single signal
    doi_match = re.search(r"\b10\.\d{4,}/\S+", text)
    if doi_match:
        score += 4
        signals.append("doi")

    # Abstract section
    if re.search(r"\babstract\b", text_lower):
        score += 2
        signals.append("abstract")

    # Standard paper section headers
    section_hits = sum(
        1 for pat in [r"\bintroduction\b", r"\bmethod", r"\bresult", r"\bconclusion",
                      r"\bdiscussion\b", r"\breferences\b", r"\backnowledg"]
        if re.search(pat, text_lower)
    )
    if section_hits >= 3:
        score += 2
        signals.append(f"sections({section_hits})")
    elif section_hits >= 1:
        score += 1

    # Known journal name
    for jpat in JOURNAL_PATTERNS:
        if re.search(jpat, text_lower):
            score += 2
            signals.append("journal_name")
            break

    # Author list patterns (e.g. "Smith J," or "Smith, J." or "Smith et al.")
    if re.search(r"[A-Z][a-z]+ [A-Z]\.,?\s+[A-Z][a-z]+|et al\.", text):
        score += 1
        signals.append("author_pattern")

    # Volume/issue/page patterns
    if re.search(r"\bvol\.?\s*\d+|issue\s+\d+|\bpp\.?\s*\d+|\bpages?\s+\d+", text_lower):
        score += 1
        signals.append("vol_issue")

    # Received/accepted/published dates
    if re.search(r"received:?|accepted:?|published:?", text_lower):
        score += 1
        signals.append("pub_dates")

    # --- Decision ---
    if score >= 6:
        confidence = "high"
    elif score >= 3:
        confidence = "medium"
    elif score >= 1:
        confidence = "low"
    else:
        return {
            "is_article": False,
            "reason": "no article signals",
            "author": "", "year": "", "tags": [], "confidence": "low",
        }

    is_article = score >= 3  # require at least medium confidence

    # --- Author extraction ---
    author = extract_author(text, metadata)

    # --- Year extraction ---
    year = extract_year(text, metadata, doi_match)

    # --- Tag assignment ---
    tags = assign_tags(combined)

    return {
        "is_article": is_article,
        "author": author,
        "year": year,
        "tags": tags,
        "confidence": confidence,
        "reason": "|".join(signals),
    }


def extract_author(text: str, metadata: dict) -> str:
    """Extract first author last name, returning ASCII lowercase."""
    # 1. PDF metadata Author field
    meta_author = metadata.get("Author", "").strip()
    if meta_author:
        # Take first author if semicolon/comma separated list
        first = re.split(r"[;,]", meta_author)[0].strip()
        # Last word is typically last name
        parts = first.split()
        if parts:
            return to_ascii_lower(parts[-1])

    # 2. Look for "Firstname Lastname" before affiliations
    #    Common patterns: "John Smith1," or "Smith, John" or "J. Smith"
    patterns = [
        # "Smith J," or "Smith, J" style (last name first)
        r"^([A-Z][a-zÀ-ÿ\-']{2,}),?\s+[A-Z]",
        # "John Smith" at start of line
        r"^[A-Z][a-z]+\s+([A-Z][a-zÀ-ÿ\-']{2,})\d*[,\s]",
        # "J. Smith" style
        r"[A-Z]\.\s+([A-Z][a-zÀ-ÿ\-']{2,})\d*[,\s]",
    ]
    for line in text.splitlines()[:60]:
        line = line.strip()
        if not line or len(line) > 120:
            continue
        for pat in patterns:
            m = re.match(pat, line)
            if m:
                candidate = m.group(1)
                # Reject common non-name words
                if candidate.lower() not in {
                    "abstract", "introduction", "methods", "results",
                    "discussion", "journal", "received", "accepted",
                    "published", "email", "copyright", "figure",
                }:
                    return to_ascii_lower(candidate)

    return ""


def extract_year(text: str, metadata: dict, doi_match) -> str:
    """Extract 4-digit publication year."""
    # 1. From DOI — many DOIs embed year: 10.1021/jacs.2023.xxxxx or similar
    if doi_match:
        m = re.search(r"\b(19|20)\d{2}\b", doi_match.group(0))
        if m:
            return m.group(0)

    # 2. PDF metadata CreationDate or ModDate
    for key in ("CreationDate", "ModDate"):
        val = metadata.get(key, "")
        m = re.search(r"(19|20)\d{2}", val)
        if m:
            yr = int(m.group(0))
            if 1990 <= yr <= 2030:
                return m.group(0)

    # 3. Received/accepted/published dates in text
    m = re.search(
        r"(?:received|accepted|published)[^\n]{0,30}(20\d{2}|19\d{2})",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1)

    # 4. Copyright year
    m = re.search(r"©\s*(20\d{2}|19\d{2})", text)
    if m:
        return m.group(1)

    # 5. Any year in range appearing in first 1000 chars
    years = re.findall(r"\b(20[0-2]\d|19[89]\d)\b", text[:1000])
    if years:
        # Prefer most common year
        from collections import Counter
        return Counter(years).most_common(1)[0][0]

    return ""


def assign_tags(text_lower: str) -> list[str]:
    """Return up to 2 matching tags based on keyword hits."""
    scores: dict[str, int] = {}
    for tag, keywords in TAG_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            scores[tag] = hits

    # Sort by hit count, return top 2
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [tag for tag, _ in ranked[:2]]


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------

def to_ascii_lower(name: str) -> str:
    """Normalize unicode name to ASCII lowercase alphanumeric."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_str = "".join(c for c in normalized if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", ascii_str.lower())


def resolve_filename(author: str, year: str, dest_dir: Path) -> Path:
    """Find a non-conflicting filename in dest_dir."""
    base = f"{author}-{year}"
    candidate = dest_dir / f"{base}.pdf"
    if not candidate.exists():
        return candidate
    for suffix in "abcdefghijklmnopqrstuvwxyz":
        candidate = dest_dir / f"{base}{suffix}.pdf"
        if not candidate.exists():
            return candidate
    n = 2
    while True:
        candidate = dest_dir / f"{base}-{n}.pdf"
        if not candidate.exists():
            return candidate
        n += 1


# ---------------------------------------------------------------------------
# Finder tag application
# ---------------------------------------------------------------------------

def apply_tag(filepath: Path, tag_names: list) -> None:
    """Apply Finder tags to a file using xattr."""
    if not tag_names:
        return
    tag_entries = [f"{name}\n{KNOWN_TAGS.get(name, '0')}" for name in tag_names]
    plist_data = plistlib.dumps(tag_entries, fmt=plistlib.FMT_BINARY)
    subprocess.run(
        ["xattr", "-wx", "com.apple.metadata:_kMDItemUserTags",
         plist_data.hex(), str(filepath)],
        check=True, capture_output=True,
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_action(csv_writer, record: dict) -> None:
    row = {field: record.get(field, "") for field in CSV_FIELDS}
    if isinstance(row["tags"], list):
        row["tags"] = "|".join(row["tags"])
    csv_writer.writerow(row)


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def process_pdf(pdf_path: Path, args, csv_writer, dest_dir: Path) -> str:
    record = {
        "source_path": str(pdf_path),
        "original_filename": pdf_path.name,
        "dest_path": "", "new_filename": "",
        "author": "", "year": "", "tags": [],
        "is_article": False, "confidence": "",
        "action": "", "error": "",
    }

    try:
        text, metadata = extract_pdf_info(pdf_path)
        if not text.strip():
            record["error"] = "no_text_extracted"

        result = classify(text, metadata)

        record.update({
            "is_article": result["is_article"],
            "confidence": result["confidence"],
            "author": result.get("author", ""),
            "year": result.get("year", ""),
            "tags": result.get("tags", []),
        })

        # Confidence threshold
        conf_order = {"high": 3, "medium": 2, "low": 1}
        min_conf = conf_order.get(args.min_confidence, 2)
        result_conf = conf_order.get(result["confidence"], 0)

        if not result["is_article"] or result_conf < min_conf:
            record["action"] = "skipped"
            reason = result.get("reason", "not_article")
            label = f"conf={result['confidence']}" if result["is_article"] else reason[:60]
            print(f"  [skip]  {pdf_path.name}  ({label})")
            log_action(csv_writer, record)
            return "skipped"

        # Validate metadata
        author = to_ascii_lower(record["author"])
        year = record["year"]
        if not author or not re.match(r"^\d{4}$", year):
            record["action"] = "error"
            record["error"] = f"bad_metadata: author='{author}' year='{year}'"
            print(f"  [error] {pdf_path.name}  (bad metadata: author='{author}' year='{year}')")
            log_action(csv_writer, record)
            return "error"

        dest_path = resolve_filename(author, year, dest_dir)
        record["dest_path"] = str(dest_path)
        record["new_filename"] = dest_path.name

        tag_str = "|".join(record["tags"]) if record["tags"] else "none"
        action_label = "dry-run" if args.dry_run else "move"
        print(f"  [{action_label}] {pdf_path.name} → {dest_path.name}  tags={tag_str}  conf={result['confidence']}")

        if args.verbose:
            print(f"           signals: {result.get('reason', '')}")

        if args.dry_run:
            record["action"] = "dry-run"
            log_action(csv_writer, record)
            return "dry-run"

        pdf_path.rename(dest_path)
        if record["tags"]:
            apply_tag(dest_path, record["tags"])

        record["action"] = "moved"
        log_action(csv_writer, record)
        return "moved"

    except Exception as e:
        record["action"] = "error"
        record["error"] = str(e)
        print(f"  [error] {pdf_path.name}  ({e})")
        log_action(csv_writer, record)
        return "error"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify PDFs in Downloads and organize journal articles (heuristics, no API)."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no files moved")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N files (0=all)")
    parser.add_argument("--downloads", type=Path, default=DEFAULT_DOWNLOADS)
    parser.add_argument("--articles", type=Path, default=DEFAULT_ARTICLES)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--min-confidence", choices=["high", "medium", "low"], default="medium",
        help="Minimum confidence to move a file (default: medium)",
    )
    args = parser.parse_args()

    if not args.downloads.is_dir():
        sys.exit(f"Downloads directory not found: {args.downloads}")
    if not args.dry_run:
        args.articles.mkdir(parents=True, exist_ok=True)

    pdfs = sorted({p for p in args.downloads.glob("*.[Pp][Dd][Ff]")})
    if args.limit:
        pdfs = pdfs[: args.limit]

    total = len(pdfs)
    print(f"Found {total} PDF(s) in {args.downloads}")
    if args.dry_run:
        print("DRY RUN — no files will be moved")
    print(f"Log: {args.log}\n")

    counts: dict[str, int] = {"moved": 0, "skipped": 0, "dry-run": 0, "error": 0}

    with open(args.log, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for i, pdf_path in enumerate(pdfs, 1):
            prefix = f"[{i}/{total}]"
            if args.verbose:
                print(f"{prefix} {pdf_path.name}")
            else:
                print(prefix, end=" ")
            action = process_pdf(pdf_path, args, writer, args.articles)
            counts[action] = counts.get(action, 0) + 1

    print(f"\n{'='*50}")
    if args.dry_run:
        print(
            f"Dry-run complete: {counts['dry-run']} would move, "
            f"{counts['skipped']} skip, {counts['error']} error"
        )
    else:
        print(f"Done: {counts['moved']} moved, {counts['skipped']} skipped, {counts['error']} errors")
    print(f"Log written to: {args.log}")


if __name__ == "__main__":
    main()
