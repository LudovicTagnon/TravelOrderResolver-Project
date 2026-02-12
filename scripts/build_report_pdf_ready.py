#!/usr/bin/env python3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    draft_path = ROOT / "docs" / "report_draft.md"
    output_path = ROOT / "docs" / "report_pdf_ready.md"

    if not draft_path.exists():
        return 1

    draft = draft_path.read_text(encoding="utf-8")
    today = date.today().isoformat()

    header = f"""---
title: "Travel Order Resolver"
subtitle: "Rapport Scientifique"
author:
  - "Ludovic Tagnon"
date: "{today}"
lang: "fr-FR"
---

# Page de garde

**Projet:** Travel Order Resolver  
**Formation:** EPITECH  
**Auteur principal:** Ludovic Tagnon  
**Version:** Draft scientifique longue  
**Date:** {today}

\\newpage

# Instructions de rendu PDF

- Format cible: ~20 pages.
- Interligne recommande: 1.15.
- Marges recommandees: 2.5 cm.
- Numeroter les tableaux et les figures.
- Inserer les figures annoncees dans `docs/figures/`.

\\newpage

"""

    output_path.write_text(header + draft, encoding="utf-8")
    print(f"output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
