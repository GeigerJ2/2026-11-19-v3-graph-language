###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Render AiiDA's flat DOT digraphs in this presentation's style, without a profile."""

import argparse
import json
import subprocess
from pathlib import Path

from graphviz import Digraph


def render(source: Path, output_dir: Path) -> Path:
    """Restyle a flat provenance digraph without changing its nodes, edges, or labels.

    :param source: an AiiDA-generated DOT file, with or without a filename extension.
    :param output_dir: directory receiving the slide-ready SVG.
    :return: the rendered SVG path.
    :raises ValueError: if the input contains subgraphs, which this renderer does not support.
    """
    # Let Graphviz parse DOT, including quoted multiline labels and escaped characters.
    result = subprocess.run(
        ['dot', '-Tjson', str(source)], capture_output=True, text=True, check=True, start_new_session=True
    )
    original = json.loads(result.stdout)
    nodes = original.get('objects', [])
    if any('nodes' in node or 'subgraphs' in node for node in nodes):
        msg = f'{source}: expected a flat AiiDA digraph, not nested subgraphs'
        raise ValueError(msg)

    graph = Digraph(
        graph_attr={
            'rankdir': 'LR',
            'bgcolor': 'transparent',
            'pad': '0.25',
            'nodesep': '0.35',
            'ranksep': '0.8',
            'splines': 'spline',
            'outputorder': 'edgesfirst',
        },
        node_attr={
            'fontname': 'Arial',
            'fontsize': '12',
            'fontcolor': '#334155',
            'color': '#cbd5e1',
            'penwidth': '1.1',
            'margin': '0.18,0.12',
            'style': 'filled',
        },
        edge_attr={
            'fontname': 'Arial',
            'fontsize': '9',
            'fontcolor': '#64748b',
            'color': '#94a3b8',
            'penwidth': '1.1',
            'arrowsize': '0.65',
        },
    )
    names = {}
    for node in nodes:
        name = node['name']
        names[node['_gvid']] = name
        label = node.get('label', name)
        attrs = {'label': label, 'shape': node.get('shape', 'ellipse'), 'fillcolor': '#ecfdf5'}
        if 'State:' in label:
            attrs.update(shape='box', style='rounded,filled', fillcolor='#fff1e6', color='#d6aa89')
        if node.get('color') == 'red':
            attrs.update(shape='box', style='rounded,filled', fillcolor='#e8f0f4', color='#5c8493', penwidth='1.8')
        elif label.startswith(('InstalledCode', 'RemoteData', 'FolderData')):
            attrs.update(fillcolor='#f1f5f9', color='#cbd5e1', fontcolor='#64748b')
        graph.node(name, **attrs)

    for edge in original.get('edges', []):
        label = edge.get('label', '')
        attrs = {'label': label, 'style': edge.get('style', 'solid')}
        if label.startswith('CALL_'):
            attrs.update(color='#8b7ca8', fontcolor='#75658f')
        elif label.startswith('RETURN'):
            attrs.update(color='#0f766e', fontcolor='#0f766e')
        graph.edge(names[edge['tail']], names[edge['head']], **attrs)

    output_dir.mkdir(parents=True, exist_ok=True)
    # Keep the source DOT and its original SVG untouched.
    target = output_dir / f'{source.stem}-slides.svg'
    target.write_bytes(graph.pipe(format='svg'))
    return target


def main() -> None:
    """Render one or more existing DOT files with the presentation palette."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', type=Path, nargs='+', help='AiiDA-generated DOT files.')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'public' / 'assets')
    args = parser.parse_args()
    for source in args.sources:
        print(render(source, args.output_dir))


if __name__ == '__main__':
    main()
