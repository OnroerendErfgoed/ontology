#!/usr/bin/env python3
"""Guard: a stable term is append-only.

A term in these vocabularies is not just a label in a file. Once something
refers to it — a database row, an exported provenance graph, an archived
dossier, another dataset — the IRI is a promise. Renaming or removing it
rewrites the meaning of records that were written years ago, silently, and
nothing fails at the moment it happens.

So this check reads the promise that is already in the files. Every term
carries ``vs:term_status`` (the W3C SemWeb vocabulary-status terms), and that
status says how much it may still move:

  unstable / testing   may still change: rename it, drop it, remodel it.
                       Whoever stores it does so at their own risk.
  stable               append-only. It may never be removed, never renamed,
                       and never demoted back to testing.
  archaic              retired. It stays in the file and stays resolvable, so
                       that what was recorded keeps meaning what it meant.
                       New data should use its successor.

Retiring a stable term is therefore `stable` -> `archaic`, ideally with a
``dct:isReplacedBy`` pointing at the successor — not a deletion.

The namespace itself has no such escape. A namespace IRI is a prefix of every
term IRI inside it, so moving it moves every term at once and there is no
per-term successor to point at. A prefix that is bound to a different IRI, or a
file whose own namespace changes, therefore always fails.

Usage:

    python scripts/check_terms_append_only.py [<git ref>]

The ref defaults to ``origin/master``, falling back to ``HEAD`` so the check is
usable as a pre-commit hook. Exit 1 on a violation. Needs ``rapper``
(raptor2-utils), the same tool ``build.sh`` uses.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

# Top level only: the vocabularies live in the repository root, while
# docs/ holds generated output. `:(glob)` keeps `*` from matching `/`.
TTL_GLOB = ":(glob)*.ttl"
STATUS = "http://www.w3.org/2003/06/sw-vocab-status/ns#term_status"
PREFERRED_NS = "http://purl.org/vocab/vann/preferredNamespaceUri"
PROTECTED = "stable"
RETIRED = "archaic"

TRIPLE = re.compile(r'^<([^>]+)>\s+<([^>]+)>\s+(.+)\s\.$')
LITERAL = re.compile(r'^"(.*)"(?:@[\w-]+|\^\^<[^>]+>)?$')
PREFIX_DECL = re.compile(r'^@prefix\s+([A-Za-z][\w-]*):\s*<([^>]+)>\s*\.', re.M)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def default_ref() -> str:
    if git("rev-parse", "--verify", "origin/master").returncode == 0:
        return "origin/master"
    return "HEAD"


def triples(ttl: str, where: str) -> list[tuple[str, str, str]]:
    """Parse Turtle into (subject, predicate, object) with rapper."""
    with tempfile.NamedTemporaryFile("w", suffix=".ttl", encoding="utf-8") as fh:
        fh.write(ttl)
        fh.flush()
        run = subprocess.run(
            ["rapper", "-q", fh.name, "-i", "turtle", "-o", "ntriples"],
            capture_output=True, text=True,
        )
    if run.returncode != 0:
        raise SystemExit(
            f"{where}: rapper could not parse this file.\n{run.stderr.strip()}"
        )
    out = []
    for line in run.stdout.splitlines():
        m = TRIPLE.match(line.strip())
        if m:
            out.append((m.group(1), m.group(2), m.group(3).strip()))
    return out


def statuses(ttl: str, where: str) -> dict[str, str]:
    """term IRI -> its declared status."""
    found = {}
    for subject, predicate, obj in triples(ttl, where):
        if predicate == STATUS:
            lit = LITERAL.match(obj)
            found[subject] = (lit.group(1) if lit else obj).strip().lower()
    return found


def own_namespace(ttl: str, where: str) -> str | None:
    for subject, predicate, obj in triples(ttl, where):
        if predicate == PREFERRED_NS:
            lit = LITERAL.match(obj)
            return lit.group(1) if lit else obj
    return None


def prefixes(ttl: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in PREFIX_DECL.finditer(ttl)}


def at_ref(ref: str, path: str) -> str | None:
    run = git("show", f"{ref}:{path}")
    return run.stdout if run.returncode == 0 else None


def compare(
    path: str, before: str, current: str, ref: str = "",
) -> tuple[list[str], int]:
    """Problems between two versions of one file, plus how many stable terms
    were checked."""
    problems: list[str] = []
    was = statuses(before, f"{ref}:{path}" if ref else f"before:{path}")
    now = statuses(current, path)

    for term, old_status in was.items():
        if old_status != PROTECTED:
            continue
        new_status = now.get(term)
        if new_status is None:
            problems.append(
                f"  {path}: stable term removed — {term}\n"
                f"      retire it with vs:term_status \"{RETIRED}\" instead, "
                f"so the IRI stays resolvable"
            )
        elif new_status not in (PROTECTED, RETIRED):
            problems.append(
                f"  {path}: stable term demoted to {new_status!r} — {term}\n"
                f"      a promise cannot be withdrawn; "
                f"\"{RETIRED}\" is the way out"
            )

    ns_was = own_namespace(before, path)
    ns_now = own_namespace(current, path)
    if ns_was and ns_now != ns_was:
        problems.append(
            f"  {path}: the file's own namespace changed — "
            f"{ns_was!r} -> {ns_now!r}\n"
            f"      every term IRI inside it moves along; there is no "
            f"per-term successor to point at"
        )

    for prefix, iri in prefixes(before).items():
        new_iri = prefixes(current).get(prefix)
        if new_iri is not None and new_iri != iri:
            problems.append(
                f"  {path}: prefix {prefix!r} re-pointed — "
                f"{iri!r} -> {new_iri!r}"
            )

    return problems, sum(1 for v in was.values() if v == PROTECTED)


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else default_ref()
    listed = git("ls-files", TTL_GLOB)
    if listed.returncode != 0:
        raise SystemExit(f"git ls-files failed:\n{listed.stderr.strip()}")
    untracked = git("ls-files", "--others", "--exclude-standard", TTL_GLOB)
    files = sorted({
        f for f in listed.stdout.splitlines() + untracked.stdout.splitlines()
        if f.strip()
    })

    problems: list[str] = []
    checked = added = 0

    for path in files:
        try:
            current = pathlib.Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            continue                      # deleted in the working tree
        before = at_ref(ref, path)
        if before is None:
            added += 1                    # a new file has nothing to compare
            continue

        found, n = compare(path, before, current, ref)
        problems += found
        checked += n

    if problems:
        print(
            "ERROR: a stable term, or a namespace, changed in a way that "
            "rewrites what has already been recorded:\n"
            + "\n".join(problems)
            + f"\n\nAdding terms is always fine. Compared against: {ref}",
            file=sys.stderr,
        )
        return 1

    print(f"OK — {checked} stable term(s) intact across {len(files)} file(s)"
          + (f", {added} new file(s) not compared" if added else "")
          + f". Compared against: {ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
