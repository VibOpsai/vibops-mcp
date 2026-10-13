"""Chaque total annonce est compare a ce qu'il y a dessous.

Le serveur expose 117 outils, et trois mesures independantes le disent : les
enregistrements de `server.py`, l'ensemble `EXPECTED_TOOLS` du test voisin, et
les lignes de tableau du `README.md`. Ce total-la est juste parce que
`scripts/check-tool-parity.sh` le compte a chaque poussee.

**Les sous-totaux, eux, n'etaient comptes par personne.** Mesure du 13/10/2026 :

    # ── Action tools (37) ──        60 outils enregistres dessous
    # ── Governance tools (27) ──    29 outils enregistres dessous

Les cinq commentaires de section sommaient a 92 pour un serveur qui en expose
117. Ecrits une fois, jamais verifies, et faux de vingt-cinq. C'est un chiffre
qui a cesse de mesurer ce qu'il annonce — le defaut le plus repete de ce depot,
ici sous sa forme la plus benigne et la plus facile a eviter.

**Ce que ce fichier ne confond pas.** `server.py` et le `README.md` ne groupent
pas les outils de la meme facon, et c'est legitime : le code groupe pour
l'auteur, la documentation pour le lecteur. `get_vm_usage` est enregistre sous
« Observation tools » et documente sous « Hypervisors », parce que c'est un
outil d'observation *de VM*. Comparer les deux decoupages terme a terme ferait
donc echouer ce test sur une difference voulue. Chaque decoupage est donc
verifie **contre lui-meme**, et seuls les totaux sont confrontes.
"""
from __future__ import annotations

import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parents[1]
SERVEUR = RACINE / "vibops_mcp" / "server.py"
README = RACINE / "README.md"

# Un enregistrement d'outil : `mcp.tool()(module.nom)`.
_ENREGISTREMENT = re.compile(r"^mcp\.tool\(\)\(\w+\.(\w+)\)", re.M)
# Une section du serveur : `# ── Action tools (60) ───…`
_SECTION = re.compile(r"^# ── (.+?) ─+\n", re.M)
# Un titre de famille du README : `### Actions (18 tools — write)`
_FAMILLE = re.compile(r"^### (.+)$", re.M)
# Une ligne de tableau d'outil : `| `list_clusters` | … |`
_LIGNE = re.compile(r"^\|\s*`([a-z_0-9]+)`\s*\|", re.M)
# Le nombre annonce entre parentheses — et les deux formes comptent, parce que
# les deux fichiers ne l'ecrivent pas pareil :
#
#   README.md   `### Actions (18 tools — write)`   -> le nombre AVANT « tools »
#   server.py   `# ── Action tools (60) ──`        -> le nombre APRES
#
# La premiere version de ce fichier ne connaissait que la forme du README. Les
# cinq sections du serveur rendaient donc `annonce = None`, la comparaison etait
# sautee, et **le controle des sections ne mesurait rien** — trouve en remettant
# le `(37)` faux et en constatant qu'aucun test ne tombait, l'empreinte du
# fichier ayant bien change. C'est le defaut que ce fichier existe pour
# attraper, commis dans ce fichier.
_ANNONCE = re.compile(r"\((\d+)\s*tools?|tools?\s*\((\d+)\)")


def _nombre_annonce(titre: str) -> int | None:
    """Le nombre annonce par un titre, quelle que soit la forme."""
    m = _ANNONCE.search(titre)
    if not m:
        return None
    return int(m.group(1) or m.group(2))


def _sections_du_serveur() -> dict[str, tuple[int | None, set[str]]]:
    """Par section : le nombre annonce (ou None) et les outils enregistres."""
    morceaux = _SECTION.split(SERVEUR.read_text(encoding="utf-8"))
    sortie: dict[str, tuple[int | None, set[str]]] = {}
    for i in range(1, len(morceaux), 2):
        titre, corps = morceaux[i].strip(), morceaux[i + 1]
        outils = set(_ENREGISTREMENT.findall(corps))
        if not outils:
            continue
        sortie[titre] = (_nombre_annonce(titre), outils)
    return sortie


def _familles_du_readme() -> dict[str, tuple[int | None, set[str]]]:
    morceaux = _FAMILLE.split(README.read_text(encoding="utf-8"))
    sortie: dict[str, tuple[int | None, set[str]]] = {}
    for i in range(1, len(morceaux), 2):
        titre, corps = morceaux[i].strip(), morceaux[i + 1]
        outils = set(_LIGNE.findall(corps))
        if not outils:
            continue
        sortie[titre] = (_nombre_annonce(titre), outils)
    return sortie


def _tous_les_outils() -> set[str]:
    return set(_ENREGISTREMENT.findall(SERVEUR.read_text(encoding="utf-8")))


# ── Le garde de recensement, d'abord ─────────────────────────────────────────

def test_the_survey_finds_the_sections_and_the_families():
    """Un scan vide declarerait tous les totaux justes.

    C'est la premiere chose a tenir : les quatre tests suivants comparent des
    nombres a des ensembles, et deux ensembles vides sont egaux. Si les
    commentaires de section changeaient de forme — un `#--` au lieu d'un
    `# ──`, un titre sans parentheses — ce fichier passerait en ne regardant
    rien.
    """
    sections, familles = _sections_du_serveur(), _familles_du_readme()
    assert len(sections) >= 5, f"sections trouvees : {list(sections)}"
    assert len(familles) >= 8, f"familles trouvees : {list(familles)}"
    assert len(_tous_les_outils()) >= 100, (
        f"seulement {len(_tous_les_outils())} enregistrements trouves : le motif "
        f"`mcp.tool()(module.nom)` ne decrit plus la facon d'enregistrer un outil"
    )


# ── Aucun regroupement ne se tait ───────────────────────────────────────────

def test_every_group_announces_a_number_at_all():
    """Un titre sans parentheses echappe a tout, et c'est le contournement.

    Les deux tests suivants comparent `annonce` au compte reel **quand il y a
    une annonce**. Retirer le `(29)` d'une section la sort donc du controle sans
    rien casser : constate en l'essayant le 13/10/2026, aucun test ne tombait.
    Celui-ci exige que tout regroupement portant des outils annonce un nombre,
    ce qui rend la seule facon de faire taire la verification aussi bruyante que
    de mentir.
    """
    muets = [
        f"server.py : {titre}"
        for titre, (annonce, _) in _sections_du_serveur().items()
        if annonce is None
    ] + [
        f"README.md : {titre}"
        for titre, (annonce, _) in _familles_du_readme().items()
        if annonce is None
    ]
    assert not muets, (
        "ces regroupements portent des outils et n'annoncent aucun nombre :\n  "
        + "\n  ".join(muets)
        + "\n\nUn titre sans parentheses sort du controle des sous-totaux. "
        "Annoncez le nombre, ou retirez le regroupement."
    )


# ── Chaque decoupage, contre lui-meme ────────────────────────────────────────

def test_each_server_section_announces_what_it_registers():
    """`# ── Action tools (60) ──` doit porter soixante enregistrements.

    Deux de ces cinq nombres etaient faux le 13/10/2026 — 37 pour 60 et 27 pour
    29 — et leur somme valait 92 pour un serveur de 117 outils.
    """
    fautifs = [
        f"{titre} : {annonce} annonce(s), {len(outils)} enregistre(s)"
        for titre, (annonce, outils) in _sections_du_serveur().items()
        if annonce is not None and annonce != len(outils)
    ]
    assert not fautifs, (
        "ces sections de `server.py` n'annoncent pas ce qu'elles portent :\n  "
        + "\n  ".join(fautifs)
        + "\n\nCorrigez le nombre entre parentheses, pas ce test."
    )


def test_each_readme_family_announces_what_it_documents():
    """`### Actions (18 tools — write)` doit porter dix-huit lignes de tableau.

    Les huit familles etaient justes a l'ecriture de ce test, et c'est ce qui
    est fige ici : elles sont ce qu'un utilisateur lit pour savoir ce que le
    serveur sait faire.
    """
    fautifs = [
        f"{titre} : {annonce} annonce(s), {len(outils)} ligne(s)"
        for titre, (annonce, outils) in _familles_du_readme().items()
        if annonce is not None and annonce != len(outils)
    ]
    assert not fautifs, (
        "ces familles du `README.md` n'annoncent pas ce qu'elles documentent :\n  "
        + "\n  ".join(fautifs)
    )


def test_every_section_total_and_every_family_total_reach_the_same_number():
    """Les deux decoupages sont differents, leur somme ne l'est pas.

    C'est le seul endroit ou les deux sont confrontes, et seulement par leur
    total : `server.py` groupe en cinq sections, le `README.md` en huit
    familles, et un outil peut legitimement changer de camp — `get_vm_usage`
    est enregistre sous « Observation » et documente sous « Hypervisors »,
    parce que c'est un outil d'observation de VM. Comparer les decoupages terme
    a terme ferait echouer ce test sur une difference voulue.
    """
    total_outils = len(_tous_les_outils())
    somme_sections = sum(len(o) for _, o in _sections_du_serveur().values())
    somme_familles = sum(len(o) for _, o in _familles_du_readme().values())

    assert somme_sections == total_outils, (
        f"les sections portent {somme_sections} outils pour "
        f"{total_outils} enregistres : un enregistrement vit hors de toute "
        f"section, donc hors de tout sous-total"
    )
    assert somme_familles == total_outils, (
        f"les familles du README documentent {somme_familles} outils pour "
        f"{total_outils} enregistres"
    )


def test_the_readme_documents_exactly_the_registered_tools():
    """Nom par nom, et c'est l'assertion la plus forte du fichier.

    Un compte juste ne dit pas que ce sont les bons outils : le README pourrait
    en citer 117 dont un inexistant et en oublier un vrai. Les deux ensembles
    etaient identiques au 13/10/2026, zero manquant et zero fantome.
    """
    enregistres = _tous_les_outils()
    documentes = set()
    for _, outils in _familles_du_readme().values():
        documentes |= outils

    absents = sorted(enregistres - documentes)
    fantomes = sorted(documentes - enregistres)
    assert not absents, (
        f"ces outils sont enregistres et ne figurent dans aucun tableau du "
        f"README : {absents}. Un utilisateur ne peut pas s'en servir s'il ne "
        f"sait pas qu'ils existent."
    )
    assert not fantomes, (
        f"ces outils sont documentes et ne sont pas enregistres : {fantomes}. "
        f"Promettre un outil absent est pire que de n'en pas parler."
    )


def test_the_badge_and_the_description_carry_the_real_total():
    """Le badge du README et la description du paquet, qui sont les plus lus.

    La description est la ligne que lit quiconque cherche `vibops-mcp` sur
    PyPI ; le badge est la premiere chose visible du depot. Ce sont les deux
    chiffres qu'on corrige en dernier parce qu'ils sont hors du code.
    """
    total = len(_tous_les_outils())
    readme = README.read_text(encoding="utf-8")

    badge = re.search(r"MCP_tools-(\d+)-", readme)
    assert badge, "le badge du nombre d'outils a disparu du README"
    assert int(badge.group(1)) == total, (
        f"le badge annonce {badge.group(1)} outils, {total} sont enregistres"
    )

    # Le texte d'introduction annonce le meme nombre, en prose.
    en_prose = re.findall(r"(\d+)\s+tools", readme)
    assert str(total) in en_prose, (
        f"aucune mention de « {total} tools » dans le README alors que c'est le "
        f"nombre enregistre ; trouve : {sorted(set(en_prose))}"
    )
