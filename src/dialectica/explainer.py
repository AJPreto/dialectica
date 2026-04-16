"""Natural-language explanation helpers for the experimental V2 path."""

from __future__ import annotations

from .engine import FOLReasoningResult, ReasoningResult, SignedLiteral
from .ir import HybridDocument


def explain_reasoning(document: HybridDocument, reasoning: ReasoningResult) -> str:
    statement_lookup = {statement.id: statement for statement in document.statements}
    lines: list[str] = []

    if reasoning.answer == "entailed":
        lines.append("The query is entailed by the Horn-compilable core of the translated document.")
    elif reasoning.answer == "blocked":
        lines.append("The query was almost derivable, but an exception guard blocked the final rule application.")
    else:
        lines.append("The query is not entailed by the Horn-compilable core of the translated document.")

    if reasoning.query is not None:
        lines.append(f"Query: `{reasoning.query.predicate}`.")

    if reasoning.trace:
        lines.append("Derivation trace:")
        for step in reasoning.trace:
            source = statement_lookup.get(step.statement_id)
            premise_text = ", ".join(item.predicate for item in step.premises) or "no premises"
            fragment = source.provenance.fragment if source is not None else step.statement_id
            lines.append(f"- `{step.derived.predicate}` from {premise_text} using: {fragment}")

    if reasoning.blocked:
        lines.append("Blocked rule applications:")
        for step in reasoning.blocked:
            source = statement_lookup.get(step.statement_id)
            blockers = ", ".join(item.predicate for item in step.blocked_by) or "an exception"
            fragment = source.provenance.fragment if source is not None else step.statement_id
            lines.append(f"- `{step.derived.predicate}` was blocked by {blockers} in: {fragment}")

    residue_lines = []
    for statement in document.statements:
        residue = statement.semantic_residue
        if residue.is_empty():
            continue
        if residue.uncertainty:
            residue_lines.append(
                f"- {statement.id}: uncertainty markers `{', '.join(residue.uncertainty)}` were preserved outside the formal core."
            )
        if residue.attribution:
            residue_lines.append(
                f"- {statement.id}: attribution `{', '.join(residue.attribution)}` was preserved as residue."
            )
        if residue.unresolved_references:
            residue_lines.append(
                f"- {statement.id}: unresolved references `{', '.join(residue.unresolved_references)}` prevented a stronger export."
            )
        if residue.non_formalized_fragments:
            residue_lines.append(f"- {statement.id}: some source text remained unformalized on purpose.")

    if residue_lines:
        lines.append("Residue that was kept explicit instead of being flattened:")
        lines.extend(residue_lines)

    if reasoning.notes:
        lines.append("Engine notes:")
        lines.extend(f"- {note}" for note in reasoning.notes)

    return "\n".join(lines)


def explain_fol_reasoning(document: HybridDocument, reasoning: FOLReasoningResult) -> str:
    statement_lookup = {statement.id: statement for statement in document.statements}
    lines: list[str] = []

    if reasoning.answer == "entailed":
        lines.append("The query is supported by the exact FOL-compilable core of the translated document.")
    elif reasoning.answer == "refuted":
        lines.append("The query is refuted by the exact FOL-compilable core of the translated document.")
    elif reasoning.answer == "conflicted":
        lines.append("The query is both supported and contradicted, so the skeptical FOL path refuses to answer yes.")
    else:
        lines.append("The query is not supported by the exact FOL-compilable core of the translated document.")

    if reasoning.query is not None:
        lines.append(f"Query: `{_literal_text(reasoning.query)}`.")

    if reasoning.trace:
        lines.append("Proof trace:")
        for step in reasoning.trace:
            source = statement_lookup.get(step.statement_id)
            premise_text = ", ".join(_literal_text(item) for item in step.premises) or "no premises"
            fragment = source.provenance.fragment if source is not None else step.statement_id
            lines.append(f"- `{_literal_text(step.derived)}` from {premise_text} using: {fragment}")

    if reasoning.blocked:
        lines.append("Blocked proof steps:")
        for step in reasoning.blocked:
            source = statement_lookup.get(step.statement_id)
            fragment = source.provenance.fragment if source is not None else step.statement_id
            if step.blocked_by:
                blockers = ", ".join(_literal_text(item) for item in step.blocked_by)
                lines.append(f"- `{_literal_text(step.derived)}` was blocked by {blockers} in: {fragment}")
            elif step.conflict_with:
                conflicts = ", ".join(_literal_text(item) for item in step.conflict_with)
                lines.append(f"- `{_literal_text(step.derived)}` was withheld because the premises are conflicted: {conflicts}")

    if reasoning.conflicts:
        lines.append("Detected conflicts:")
        for literal in reasoning.conflicts:
            lines.append(f"- `{_literal_text(literal)}` conflicts with its negation.")

    residue_lines = []
    for statement in document.statements:
        residue = statement.semantic_residue
        if residue.is_empty():
            continue
        if residue.uncertainty:
            residue_lines.append(
                f"- {statement.id}: uncertainty markers `{', '.join(residue.uncertainty)}` were preserved outside the exact proof core."
            )
        if residue.attribution:
            residue_lines.append(
                f"- {statement.id}: attribution `{', '.join(residue.attribution)}` prevented promotion to settled fact status."
            )
        if residue.unresolved_references:
            residue_lines.append(
                f"- {statement.id}: unresolved references `{', '.join(residue.unresolved_references)}` prevented a stronger export."
            )
        if residue.non_formalized_fragments:
            residue_lines.append(f"- {statement.id}: some source text remained outside the exact proof core on purpose.")

    if residue_lines:
        lines.append("Residue that remained explicit:")
        lines.extend(residue_lines)

    if reasoning.notes:
        lines.append("Engine notes:")
        lines.extend(f"- {note}" for note in reasoning.notes)

    return "\n".join(lines)


def _literal_text(literal: SignedLiteral) -> str:
    return literal.text()
