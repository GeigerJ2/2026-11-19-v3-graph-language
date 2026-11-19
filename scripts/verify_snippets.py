###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Check snippet coverage, Python syntax, source regions, and rendered provenance integrity."""

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree

from sync_slide_code import EXCERPTS, sync

HERE = Path(__file__).resolve().parent


def check_sources() -> None:
    """Verify that every inventoried snippet is referenced by the slides and parses as Python."""
    slides = (HERE.parent / 'slides.md').read_text()
    assert '```python' not in slides
    assert '```text' not in slides
    assert '<pre class="concept-code"><code>' not in slides
    inventory = json.loads((HERE / 'snippets.json').read_text())
    sync(check=True)
    referenced = set()
    for filename, region in re.findall(r'^<<< @/scripts/([^#\s]+)(?:#([\w-]+))?', slides, re.M):
        source = (HERE / filename).read_text()
        if region:
            assert re.search(rf'^\s*# region {re.escape(region)}\s*$', source, re.M), (filename, region)
            assert re.search(rf'^\s*# endregion {re.escape(region)}\s*$', source, re.M), (filename, region)
        referenced.add(filename)
    for filename, region in re.findall(r'<ConceptCode file="([^"]+)" region="([^"]+)"', slides):
        source = (HERE / filename).read_text()
        assert f'# region {region}\n' in source
        assert f'# endregion {region}' in source
        referenced.add(filename)
    for filename, region in re.findall(r'append-file="([^"]+)" append-region="([^"]+)"', slides):
        source = (HERE / filename).read_text()
        assert f'# region {region}\n' in source
        assert f'# endregion {region}' in source
        referenced.add(filename)
    for name, sources in EXCERPTS.items():
        assert f'generated/{name}' in referenced
        referenced.update(sources)
    for item in inventory['snippets'] + inventory['concepts']:
        assert item['file'] in referenced, f'Unreferenced snippet: {item["file"]}'
    for source in HERE.glob('*.py'):
        ast.parse(source.read_text(), filename=str(source))
    for target in re.findall(r'<img[^>]+src="(/assets/[^"]+)"', slides):
        assert (HERE.parent / 'public' / target.lstrip('/')).is_file(), target
    print(
        f'Validated {len(inventory["snippets"])} Python snippets, '
        f'{len(inventory["concepts"])} concept fragments, two diagnostic excerpts, and all diagram references.'
    )


def check_diagrams() -> None:
    """Verify that styled SVGs retain the AiiDA-generated DOT node and edge sets."""
    results = json.loads((HERE / 'generated/results.json').read_text())
    assert results.get('completed'), 'The last execution did not complete; inspect results.json and rerun.'
    for record in results['runs']:
        dot = HERE.parent / record['dot']
        svg = HERE.parent / record['svg']
        parsed = subprocess.run(
            ['dot', '-Tjson', str(dot)], capture_output=True, text=True, check=True, start_new_session=True
        )
        original = json.loads(parsed.stdout)
        root = ElementTree.parse(svg).getroot()
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        nodes = root.findall('.//svg:g[@class="node"]', ns)
        edges = root.findall('.//svg:g[@class="edge"]', ns)
        assert {node.findtext('svg:title', namespaces=ns) for node in nodes} == {
            node['name'] for node in original.get('objects', [])
        }, record['case']
        assert len(edges) == len(original.get('edges', [])), record['case']
        assert record['root_pk'] is not None
    print(f'Validated {len(results["runs"])} real-provenance SVGs against their source DOT graphs.')


def main() -> None:
    """Validate sources, optionally also checking previously rendered diagrams."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-only', action='store_true')
    args = parser.parse_args()
    check_sources()
    if not args.sources_only:
        check_diagrams()


if __name__ == '__main__':
    main()
