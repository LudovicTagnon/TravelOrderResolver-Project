#!/usr/bin/env python3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current_title:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = [line]
        else:
            if current_title:
                current_lines.append(line)
    if current_title:
        sections.append((current_title, current_lines))
    return sections


def pick_sections(
    sections: list[tuple[str, list[str]]],
    prefixes: list[str],
) -> list[list[str]]:
    picked: list[list[str]] = []
    for prefix in prefixes:
        found = None
        for title, content in sections:
            if title.startswith(prefix):
                found = content
                break
        if found is not None:
            picked.append(found)
    return picked


def main() -> int:
    draft_path = ROOT / "docs" / "report_draft.md"
    output_path = ROOT / "docs" / "report_jury_ready.md"

    if not draft_path.exists():
        return 1

    lines = draft_path.read_text(encoding="utf-8").splitlines()
    sections = parse_sections(lines)

    selected_prefixes = [
        "Resume",
        "1. Introduction",
        "2. Problematique et contraintes",
        "3. Questions de recherche",
        "4. Strategie de realisation",
        "5. Jeux de donnees",
        "6. Architecture technique",
        "7. Methodologie experimentale",
        "8. Approche rule-based",
        "9. Baseline ML classique",
        "10. Benchmarks spaCy",
        "11. CamemBERT fine-tune",
        "12. Pathfinding",
        "13. Evaluation end-to-end",
        "14. Analyse d'erreurs",
        "15. Challenges techniques et strategie",
        "16. Discussion technique",
        "17. Validite et limites",
        "18. Reproductibilite et artefacts",
        "19. Etat actuel et plan avant soutenance",
        "20. Conclusion",
        "22. Comparaison quantitative multi-niveaux",
        "23. Retours d'experience",
        "24. Couts, risques et compromis",
        "25. Protocole de soutenance technique",
        "26. Extensions envisagees",
        "Annexe A - Commandes de reproduction",
        "Annexe B - Tableau comparatif principal",
        "Annexe C - Journal de decisions",
    ]
    picked_sections = pick_sections(sections, selected_prefixes)

    today = date.today().isoformat()
    header = f"""---
title: "Travel Order Resolver"
subtitle: "Rapport Scientifique - Version Jury"
author:
  - "Ludovic Tagnon"
date: "{today}"
lang: "fr-FR"
---

# Page de garde

**Projet:** Travel Order Resolver  
**Formation:** EPITECH  
**Auteur principal:** Ludovic Tagnon  
**Version:** Jury (compacte)  
**Date:** {today}

\\newpage

# Sommaire visuel recommande

- Figure 1: Architecture globale (`docs/figures/figure_1_architecture.png`)
- Figure 2: Flux de donnees (`docs/figures/figure_2_dataflow.png`)
- Figure 3: Evolution metriques (`docs/figures/figure_3_metrics_evolution.png`)
- Figure 4: Taxonomie d'erreurs (`docs/figures/figure_4_error_taxonomy.png`)

\\newpage

"""

    body = []
    for section_lines in picked_sections:
        body.extend(section_lines)
        if section_lines and section_lines[-1] != "":
            body.append("")

    output_path.write_text(header + "\n".join(body) + "\n", encoding="utf-8")
    print(f"output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
