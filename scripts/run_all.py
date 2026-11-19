###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Validate slide snippets and render real provenance using render_provenance.py."""

import argparse
import html
import importlib
import json
import math
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_execution_profile(profile: str | None) -> str:
    """Load an explicit profile, or create a fresh service-free profile outside the repository.

    :param profile: existing profile name, or None for an isolated SQLite profile.
    :return: the active configuration directory, retained for inspecting the stored nodes.
    """
    if profile is None:
        configuration = Path(tempfile.mkdtemp(prefix='aiida-slide-snippets-'))
        os.environ['AIIDA_PATH'] = str(configuration)
        from aiida.manage.configuration import create_profile, get_config
        from aiida.manage.configuration.settings import AiiDAConfigDir

        # Individual snippet entry points may already have imported AiiDA.
        AiiDAConfigDir.set(configuration / '.aiida')
        config = get_config(create=True)
        created = create_profile(
            config,
            name='slide-snippets',
            email='slides@localhost',
            storage_backend='core.sqlite_dos',
            storage_config={'filepath': str(configuration / 'storage')},
            broker_backend=None,
        )
        created.set_option('warnings.development_version', False)
        config.set_default_profile(created.name)
        config.store()
        profile = created.name
    from aiida import load_profile
    from aiida.manage.configuration import get_config

    load_profile(profile)
    return str(get_config().dirpath)


class Examples:
    """Run assertions and retain each real process root beside its diagram paths."""

    def __init__(self, output_dir: Path, assets_dir: Path) -> None:
        self.output_dir = output_dir
        self.assets_dir = assets_dir
        self.records: list[dict] = []

    def save(self, snippet: int, name: str, node, result=None) -> None:
        """Render actual stored provenance without dropping nodes or links."""
        from render_provenance import render

        from aiida.tools.visualization import Graph

        self.output_dir.mkdir(parents=True, exist_ok=True)
        graph = Graph(graph_attr={'rankdir': 'LR'})
        graph.recurse_descendants(node, annotate_links='both', include_process_inputs=True)
        stem = f's{snippet:02d}_{name}'
        dot = Path(graph.graphviz.save(filename=f'{stem}.dot', directory=str(self.output_dir)))
        svg = render(dot, self.assets_dir)
        record = {
            'snippet': snippet,
            'case': name,
            'root_pk': node.pk,
            'root_uuid': node.uuid,
            'state': str(node.process_state),
            'exit_status': node.exit_status,
            'result': result,
            'dot': os.path.relpath(dot, HERE.parent),
            'svg': os.path.relpath(svg, HERE.parent),
        }
        self.records.append(record)
        print(f'{stem}: pk={node.pk} exit={node.exit_status} result={result} -> {svg}', flush=True)

    def run(self, snippet: int, name: str, target, expected, *, inputs=None, runtime_config=None) -> None:
        """Build a graph, execute it, assert the result and render its provenance."""
        from aiida.engine import run_get_node

        if hasattr(target, 'build'):
            assert target.build() is None
        if runtime_config is None:
            outputs, node = run_get_node(target, **(inputs or {}))
        else:
            outputs, node = run_get_node(target, inputs=inputs or {}, runtime_config=runtime_config)
        self.check(snippet, name, outputs, node, expected)

    def check(self, snippet: int, name: str, outputs, node, expected) -> None:
        """Check scalar or structure-list output, then render its stored root."""
        assert node.is_finished_ok, f'{name}: {node.process_state}, exit={node.exit_status}'
        value = outputs['result'] if isinstance(outputs, Mapping) else outputs
        value = value.value if hasattr(value, 'value') else value
        if isinstance(expected, float):
            assert math.isclose(value, expected, rel_tol=1e-10), (value, expected)
        else:
            assert value == expected, (value, expected)
        self.save(snippet, name, node, value)

    def expected_workchain_exception(self, module) -> None:
        """Run and render the WorkChain whose missing context entry raises AttributeError."""
        from aiida.manage import get_manager
        from aiida.orm import Bool, Int

        runner = get_manager().get_runner()
        process = runner.instantiate_process(module.ConditionalCtxChain, value=Int(4), flag=Bool(False))
        try:
            runner.run_get_node(process)
        except AttributeError as error:
            assert 'total' in str(error)
        else:
            msg = 'Expected the WorkChain to fail on its missing ctx.total.'
            raise AssertionError(msg)
        assert process.node.is_excepted
        self.save(3, 'missing_context', process.node)


def execute(examples: Examples, selected: set[int], manifest: list[dict]) -> list[dict]:
    """Run representative successes, both branches, retries, and expected failures.

    :param examples: execution and rendering context.
    :param selected: snippet identifiers to exercise.
    :param manifest: source-file and status inventory.
    :return: validation notes for non-executable or shared snippets.
    """
    from support import ensure_code

    from aiida.common.exceptions import GraphLanguageError
    from aiida.engine import run_get_node
    from aiida.orm import Bool, DataList, Int, StructureData

    modules = {item['id']: item['file'].removesuffix('.py') for item in manifest}
    notes = []
    # Definition-only snippets are exercised through the graphs that use them.
    owners = {13: 14, 15: 16, 17: 18, 19: 20, 21: 22}
    selected = selected | {owner for definition, owner in owners.items() if definition in selected}
    for identifier in sorted(selected):
        module = importlib.import_module(modules[identifier])
        if identifier in owners:
            notes.append({'snippet': identifier, 'status': 'exercised-by', 'snippet_id': owners[identifier]})
            continue
        if identifier in (25, 26):
            notes.append(
                {
                    'snippet': identifier,
                    'status': 'reference-only',
                    'reason': (
                        'WorkGraph builder fragment, not an AiiDA graph-language workflow. No fabricated provenance.'
                    ),
                }
            )
            continue
        if identifier == 28:
            notes.append(
                {
                    'snippet': identifier,
                    'status': 'unimplemented-proposal',
                    'reason': 'checkpoint() is not implemented. No execution or provenance is claimed.',
                }
            )
            continue
        if identifier == 1:
            examples.run(
                identifier,
                'multiply_add_workchain',
                module.MultiplyAddWorkChain,
                10,
                inputs={'x': Int(2), 'y': Int(3), 'z': Int(4), 'code': ensure_code()},
            )
        elif identifier == 2:
            examples.run(
                identifier,
                'multiply_add_graph',
                module.multiply_add,
                10,
                inputs={'x': 2, 'y': 3, 'z': 4, 'code': ensure_code()},
            )
        elif identifier == 3:
            examples.run(
                identifier, 'with_context', module.ConditionalCtxChain, 5, inputs={'value': Int(4), 'flag': Bool(True)}
            )
            examples.expected_workchain_exception(module)
        elif identifier == 4:
            try:
                module.demonstrate_build_error()
            except GraphLanguageError as error:
                assert 'total' in str(error)
                notes.append({'snippet': identifier, 'status': 'expected-build-error', 'diagnostic': str(error)})
                print(f's04: expected build rejection: {error}', flush=True)
            else:
                msg = 'The broken graph unexpectedly built.'
                raise AssertionError(msg)
        elif identifier in (5, 6):
            for flag in (True, False):
                expected = 11 if flag else (10 if identifier == 5 else 12)
                examples.run(
                    identifier, f'flag_{str(flag).lower()}', module.fixed, expected, inputs={'value': 10, 'flag': flag}
                )
        elif identifier in (7, 8, 11, 12, 29, 34, 35):
            names = {
                7: 'multiply_add_task',
                8: 'stored_inline',
                11: 'calculate',
                12: 'calculate',
                29: 'arithmetic_inline',
                34: 'arithmetic_task',
                35: 'arithmetic_inline',
            }
            expected = 20 if identifier in (29, 34, 35) else 10
            examples.run(
                identifier,
                names[identifier],
                getattr(module, names[identifier]),
                expected,
                inputs={'x': 2, 'y': 3, 'z': 4},
            )
            if identifier == 29:
                notes.append(
                    {
                        'snippet': identifier,
                        'status': 'baseline-only',
                        'reason': 'Executed current behavior, not proposed per-statement checkpointing.',
                    }
                )
        elif identifier in (9, 10):
            target = module.summarize if identifier == 9 else module.analyze
            examples.run(identifier, 'finite_mean', target, 2.0, inputs={'values': [1.0, 2.0, 3.0]})
        elif identifier == 14:
            lattices = (2.0, 3.0, 4.0)
            structures = DataList[StructureData](
                [StructureData(cell=[[side, 0, 0], [0, side, 0], [0, 0, side]]) for side in lattices]
            )
            examples.run(
                identifier,
                'mean_expanded_volume',
                module.mean_expanded_volume,
                38.201625,
                inputs={'structures': structures},
            )
            assert all(
                math.isclose(item.get_cell_volume(), side**3) for item, side in zip(structures, lattices, strict=True)
            )
        elif identifier == 16:
            examples.run(identifier, 'two_steps', module.two_steps, 8, inputs={'x': 2, 'y': 3})
            try:
                module.add_shifted.build()
            except GraphLanguageError as error:
                assert 'partial' in str(error)
                notes.append(
                    {
                        'snippet': identifier,
                        'status': 'partially-supported',
                        'reason': 'Placement aliases execute; partial bindings are not supported in this checkout.',
                        'diagnostic': str(error),
                    }
                )
            else:
                msg = 'Partial bindings are now supported; add their execution case to this runner.'
                raise AssertionError(msg)
        elif identifier == 18:
            outputs, node = module.demo()
            examples.check(identifier, 'configured_defaults', outputs, node, 11.57625)
        elif identifier == 20:
            ensure_code()
            outputs, node = module.demo()
            examples.check(identifier, 'integrated', outputs, node, 14)
        elif identifier == 22:
            for denominator in (0.0, 3.0):
                examples.run(
                    identifier,
                    f'denominator_{int(denominator)}',
                    module.stored_ratio_or_zero,
                    0.0 if denominator == 0 else 4.0,
                    inputs={'numerator': 12.0, 'denominator': denominator},
                )
        elif identifier == 24:
            for denominator in (0.0, 3.0):
                examples.run(
                    identifier,
                    f'denominator_{int(denominator)}',
                    module.retry_ratio,
                    12.0 if denominator == 0 else 4.0,
                    inputs={'numerator': 12.0, 'denominator': denominator, 'max_retries': 3},
                )
            outputs, node = run_get_node(module.retry_ratio, numerator=12.0, denominator=0.0, max_retries=0)
            assert node.is_finished_ok
            assert not outputs
            examples.save(identifier, 'exhausted_budget_no_output', node)
        elif identifier == 27:
            for value, expected in ((-2, 1), (2, 7)):
                examples.run(
                    identifier, f'input_{value}', module.selected_branch, expected, inputs={'first_sum': value}
                )
        elif identifier in (30, 31, 32, 33):
            target = module.choose_task if identifier in (30, 32) else module.choose_graph
            for value, expected in ((-2, 1), (2, 6)):
                examples.run(identifier, f'input_{value}', target, expected, inputs={'x': value, 'y': 3})
        else:
            msg = f'Missing execution policy for snippet {identifier}.'
            raise AssertionError(msg)
    return notes


def write_summary(results: dict, output_dir: Path, assets_dir: Path) -> None:
    """Index the rendered diagrams and validation exceptions.

    :param results: execution inventory including source status notes.
    :param output_dir: directory receiving the Markdown index.
    :param assets_dir: directory receiving a browsable SVG gallery.
    """
    lines = [
        '# Verified slide provenance',
        '',
        'Generated by `../run_all.py` from real stored AiiDA process roots.',
        '',
        '| Snippet | Case | Root PK | Exit status | Diagram |',
        '| --- | --- | --- | --- | --- |',
    ]
    figures = []
    for record in results['runs']:
        svg = HERE.parent / record['svg']
        link = os.path.relpath(svg, output_dir)
        lines.append(
            f'| {record["snippet"]:02d} | {record["case"]} | {record["root_pk"]} | '
            f'{record["exit_status"]} | [SVG]({link}) |'
        )
        caption = html.escape(f'{record["snippet"]:02d}: {record["case"]} (root PK {record["root_pk"]})')
        image = html.escape(os.path.relpath(svg, assets_dir), quote=True)
        figures.append(
            f'<figure><figcaption>{caption}</figcaption><a href="{image}">'
            f'<img src="{image}" alt="{caption}" loading="lazy"></a></figure>'
        )
    lines.extend(['', '## Validation notes', ''])
    for note in results['notes']:
        reason = note.get('reason', note.get('diagnostic', f'Exercised by snippet {note.get("snippet_id")}.'))
        lines.append(f'- **{note["snippet"]:02d} — {note["status"]}:** {reason}')
    (output_dir / 'README.md').write_text('\n'.join(lines) + '\n')
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / 'index.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Verified slide provenance</title><style>'
        'body{font:16px system-ui;margin:2rem;color:#334155;background:#f8fafc}'
        'figure{margin:2rem 0;padding:1rem;background:white;border:1px solid #cbd5e1;border-radius:12px}'
        'figcaption{font-weight:600;margin-bottom:1rem}img{max-width:100%;max-height:600px}'
        '</style><h1>Verified slide provenance</h1>'
        '<p>Real AiiDA nodes and links, styled by render_provenance.py. Click a diagram for its SVG.</p>'
        + '\n'.join(figures)
        + '</html>\n'
    )


def main(default_snippet: int | None = None) -> None:
    """Execute all supported snippets, or one snippet selected from its standalone script.

    :param default_snippet: select this snippet when invoked from an individual example.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', help='Existing profile to use; omitted creates a fresh isolated SQLite profile.')
    parser.add_argument('--snippet', type=int, nargs='+', help='Snippet IDs to run (default: all).')
    parser.add_argument('--output-dir', type=Path, default=HERE / 'generated')
    parser.add_argument('--assets-dir', type=Path, default=HERE.parent / 'public/assets/provenance')
    args = parser.parse_args()
    source = json.loads((HERE / 'snippets.json').read_text())
    selected = set(
        args.snippet or ([default_snippet] if default_snippet else [item['id'] for item in source['snippets']])
    )
    known = {item['id'] for item in source['snippets']}
    if selected - known:
        parser.error(f'Unknown snippet IDs: {sorted(selected - known)}')
    profile_path = load_execution_profile(args.profile)
    print(f'AiiDA configuration retained at {profile_path}', flush=True)
    examples = Examples(args.output_dir.resolve(), args.assets_dir.resolve())
    try:
        notes = execute(examples, selected, source['snippets'])
    finally:
        # Preserve a partial inventory if a real regression interrupts the run.
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / 'results.json').write_text(
            json.dumps(
                {
                    'completed': False,
                    'configuration': profile_path,
                    'selected_snippets': sorted(selected),
                    'runs': examples.records,
                },
                indent=2,
            )
            + '\n'
        )
    results = json.loads((args.output_dir / 'results.json').read_text())
    results['completed'] = True
    results['notes'] = notes
    results['concepts'] = source['concepts']
    (args.output_dir / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    write_summary(results, args.output_dir.resolve(), args.assets_dir.resolve())
    print(f'Completed: {len(examples.records)} stored-provenance SVGs; {len(notes)} validation notes.', flush=True)


if __name__ == '__main__':
    main()
