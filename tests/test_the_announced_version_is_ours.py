"""Le serveur annonce sa version, et non celle de la bibliotheque qui le porte.

Mesure du 13/10/2026, en parlant MCP au binaire fraichement installe depuis
PyPI — `initialize` sur l'entree standard, reponse lue sur la sortie :

    serverInfo {"name": "vibops", "version": "1.30.0"}

`1.30.0` est la version du **SDK `mcp`**, pas celle de ce paquet, qui etait en
0.55.3. `FastMCP` n'a pas de parametre `version` (sa signature en 1.30.0 accepte
`name`, `instructions`, `website_url`, `icons` et vingt autres, pas celui-la) ;
le serveur bas niveau l'accepte et il vaut `None` par defaut, et c'est ce `None`
qui fait retomber la bibliotheque sur la sienne.

Un client qui se connectait lisait donc un numero qui ne disait rien de ce
produit. Rien n'etait casse — et c'est bien le probleme : un champ qui existe,
qui est rempli, et qui n'informe pas.

**Ce que ce fichier tient, et pourquoi par ce chemin.** `server.py` affecte la
version a travers un attribut prive, `mcp._mcp_server.version`, faute de voie
publique. Ce test n'assertionne pas l'affectation — il interroge
`create_initialization_options()`, c'est-a-dire la methode que la bibliotheque
appelle elle-meme pour construire la reponse a `initialize`. Si elle renomme son
interne, ce test tombe, au lieu de laisser le serveur annoncer en silence la
version de quelqu'un d'autre. Un test sur l'affectation passerait dans ce cas-la.
"""
from __future__ import annotations

import pathlib
import re

import vibops_mcp.server as serveur
from vibops_mcp import __version__

RACINE = pathlib.Path(__file__).resolve().parents[1]


def test_the_handshake_announces_the_package_version():
    """Le chemin que la bibliotheque emprunte vraiment, pas l'attribut."""
    options = serveur.mcp._mcp_server.create_initialization_options()

    assert options.server_version == __version__, (
        f"le serveur annonce « {options.server_version} » et le paquet est en "
        f"« {__version__} ». Si c'est la version du SDK `mcp`, l'affectation de "
        f"`mcp._mcp_server.version` dans `server.py` ne prend plus — la "
        f"bibliotheque a probablement renomme son interne."
    )
    assert options.server_name == "vibops", (
        f"le serveur s'annonce « {options.server_name} » : c'est le nom qu'un "
        f"client affiche dans sa liste de serveurs"
    )


def test_the_announced_version_is_the_one_the_release_script_writes():
    """Et cette version est bien celle que `bump-version.sh` tient a jour.

    Sans ce bout, le serveur pourrait annoncer une version coherente avec
    `__init__.py` et toutes deux derivees de `pyproject.toml` — le paquet
    installe dirait une chose et la poignee de main une autre. Les trois doivent
    etre le meme nombre, et c'est `scripts/bump-version.sh` qui le garantit en
    les ecrivant ensemble.
    """
    projet = (RACINE / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', projet, flags=re.M)
    assert m, "`version` a disparu de `mcp/pyproject.toml`"
    assert m.group(1) == __version__, (
        f"`pyproject.toml` dit {m.group(1)} et `__init__.py` dit {__version__}. "
        f"Lancez `scripts/bump-version.sh` : il ecrit les treize emplacements "
        f"ensemble, et c'est la seule facon qu'ils ne divergent pas."
    )


def test_the_version_is_not_the_mcp_library_version():
    """Le temoin negatif, qui nomme le defaut d'origine.

    Les deux tests ci-dessus passeraient si, par coincidence, ce paquet
    atteignait un jour la meme version que le SDK. Celui-ci dit explicitement
    quelle valeur etait annoncee a tort, pour que l'intention reste lisible le
    jour ou quelqu'un se demande pourquoi `server.py` touche un attribut prive.
    """
    import mcp as bibliotheque

    version_sdk = getattr(bibliotheque, "__version__", None)
    options = serveur.mcp._mcp_server.create_initialization_options()
    if version_sdk and version_sdk != __version__:
        assert options.server_version != version_sdk, (
            f"le serveur annonce {version_sdk}, la version du SDK `mcp` — "
            f"c'est exactement le defaut du 13/10/2026 : `version` vaut `None` "
            f"sur le serveur bas niveau et la bibliotheque remplit le champ "
            f"avec le sien."
        )
