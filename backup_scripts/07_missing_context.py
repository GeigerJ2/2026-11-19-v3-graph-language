###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 07: a valid spec with a missing context value on one path.

``ConditionalCtxChain`` only fills ``ctx.total`` when ``flag`` is true, so the
``flag=False`` path fails at runtime with ``AttributeError``. Both the
successful and the failed roots are rendered to SVG.
"""

import argparse
from pathlib import Path

from aiida.engine import WorkChain, calcfunction, if_, run_get_node
from aiida.engine.processes.workchains.workchain import WorkChainSpec
from aiida.orm import Bool, Int, ProcessNode


@calcfunction
def increment(value: int) -> int:
    """Return ``value + 1`` as a stored calculation."""
    return value + 1


class ConditionalCtxChain(WorkChain):
    """Add one on the guarded path, then report the context value."""

    @classmethod
    def define(cls, spec: WorkChainSpec) -> None:  # type: ignore[override]  # The engine narrows generic process specs.
        """Specify inputs, outline and outputs."""
        super().define(spec)
        spec.input('value', valid_type=Int)
        spec.input('flag', valid_type=Bool)
        spec.outline(
            if_(cls.should_add)(cls.add_one),
            cls.finish,
        )
        spec.output('result', valid_type=Int)

    def should_add(self: WorkChain) -> bool:
        """Return whether the guarded step should run."""
        return self.inputs.flag.value

    def add_one(self: WorkChain) -> None:
        """Store the incremented value in the context."""
        self.ctx.total = increment(self.inputs.value)

    def finish(self: WorkChain) -> None:
        """Expose the context value as the workflow result."""
        self.out('result', self.ctx.total)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    :return: the parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='graph-examples', help='AiiDA profile to load.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).resolve().parent / 'generated',
        help='Directory for the rendered SVG provenance.',
    )
    return parser.parse_args()


def render_provenance(root: ProcessNode, output_dir: Path, stem: str) -> str:
    """Render the provenance of ``root`` to an SVG file.

    :param root: the workflow node to visualize.
    :param output_dir: directory receiving the rendered file.
    :param stem: filename stem (without extension) for the rendering.
    :return: the path of the rendered SVG file.
    """
    from aiida.tools.visualization import Graph

    output_dir.mkdir(parents=True, exist_ok=True)
    viz = Graph(graph_attr={'rankdir': 'LR'})
    viz.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
    return str(viz.graphviz.render(filename=stem, directory=str(output_dir), format='svg', cleanup=False))


def main() -> None:
    """Run the true (success) and false (``AttributeError``) paths."""
    from aiida import load_profile
    from aiida.manage import get_manager

    args = parse_args()
    load_profile(args.profile)

    outputs, success = run_get_node(ConditionalCtxChain, value=Int(4), flag=Bool(True))
    assert success.is_finished_ok
    assert outputs['result'].value == 5
    success_path = render_provenance(success, args.output_dir, '07_conditional_true')
    print(f'true-path<{success.pk}> finished: {success.is_finished_ok} result=5 path={success_path}')

    runner = get_manager().get_runner()
    failed_process = runner.instantiate_process(ConditionalCtxChain, value=Int(4), flag=Bool(False))
    try:
        runner.run_get_node(failed_process)
    except AttributeError as exc:
        if 'total' not in str(exc):
            raise
        failed = failed_process.node
    else:
        msg = 'flag=False unexpectedly succeeded; expected AttributeError for missing ctx.total'
        raise AssertionError(msg)

    assert failed.is_excepted
    failed_path = render_provenance(failed, args.output_dir, '07_conditional_false')
    print(f'false-path<{failed.pk}> excepted: {failed.is_excepted} path={failed_path}')


if __name__ == '__main__':
    main()
