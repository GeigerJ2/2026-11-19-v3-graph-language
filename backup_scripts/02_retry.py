###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 02: bounded retry of a declared failure with ``restartable``.

``run_step`` reports the declared ``StepErrors.UNSTABLE`` failure for the
first two attempts and succeeds afterwards. The graph retries only that
member while the ``max_retries`` budget lasts; ``ensure`` fails the graph
when no attempt succeeded. Both the recovered run and the exhausted run
are executed and their provenance is rendered with the AiiDA ``Graph``
visualizer.
"""

import argparse
from pathlib import Path

from aiida import load_profile
from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result, graph, run_get_node, task
from aiida.orm import ProcessNode
from aiida.tools.visualization import Graph


class StepErrors(ExitCodeEnum):
    """Declared failures of the ``run_step`` task."""

    UNSTABLE = ExitCode(410, 'Unstable step.')


@task
def run_step(x: int, attempt: int) -> Result[int, StepErrors]:
    """Carry ``x`` through once stable, failing the first two attempts.

    :param x: the value the step carries on success.
    :param attempt: the zero-based attempt number.
    :return: ``Err(StepErrors.UNSTABLE)`` while ``attempt < 2``, else ``Ok(x)``.
    """
    if attempt < 2:
        return Err(StepErrors.UNSTABLE)
    return Ok(x)


@task
def ensure(value: int | None) -> None:
    """Validate as a side effect that an attempt succeeded.

    :param value: the recovered value, ``None`` when every attempt failed.
    :raises ValueError: if no attempt succeeded.
    """
    if value is None:
        msg = 'the step never succeeded.'
        raise ValueError(msg)


@graph
def restartable(x: int, max_retries: int, attempt: int = 0) -> int:
    """Retry the unstable step while the failure is declared and budget lasts.

    :param x: the value the step carries on success.
    :param max_retries: repeats allowed after the first call.
    :param attempt: the zero-based attempt the first run steps from.
    :return: the successful step output.
    """
    value, error = run_step(x=x, attempt=attempt)
    while error is StepErrors.UNSTABLE and attempt < max_retries:
        attempt = attempt + 1
        value, error = run_step(x=x, attempt=attempt)
    checked = ensure(value=value)  # noqa: F841 - the guard validates without feeding the return
    return value


def render_provenance(root: ProcessNode, stem: str, output_dir: Path) -> Path:
    """Render the stored provenance of ``root`` to an SVG file.

    Works for finished and failed roots alike, so the exhausted run
    keeps its provenance diagram.

    :param root: the stored graph process node to visualize.
    :param stem: the filename stem, without extension.
    :param output_dir: the directory receiving the rendered file.
    :return: the path of the rendered SVG file.
    """
    provenance = Graph(graph_attr={'rankdir': 'LR'})
    provenance.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
    rendered = provenance.graphviz.render(filename=stem, directory=str(output_dir), format='svg', cleanup=False)
    return Path(rendered)


def main() -> None:
    """Validate, run, and visualize the recovered and exhausted retries."""
    parser = argparse.ArgumentParser(description='Run slide 02: bounded retry.')
    parser.add_argument('--profile', default='graph-examples', help='The AiiDA profile to load.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).resolve().parent / 'generated',
        help='The directory receiving the rendered SVG files.',
    )
    args = parser.parse_args()

    load_profile(args.profile)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    restartable.build()

    outputs, root = run_get_node(restartable, x=10, max_retries=2)
    assert root.is_finished_ok
    assert outputs['result'].value == 10
    svg = render_provenance(root, '02-restartable-recovered', args.output_dir)
    print(f'restartable(x=10, max_retries=2): root pk={root.pk}, result=10, svg={svg}')

    outputs, failed_root = run_get_node(restartable, x=10, max_retries=0)
    # The exhausted budget is the documented ERROR_TASK_FAILED failure: the
    # `ensure` guard raises because the single attempt never succeeded.
    # Matching the exact exit status keeps unexpected failures loud.
    assert not failed_root.is_finished_ok
    assert failed_root.exit_status == 400
    assert outputs == {}
    failed_svg = render_provenance(failed_root, '02-restartable-exhausted', args.output_dir)
    print(
        f'restartable(x=10, max_retries=0): root pk={failed_root.pk}, '
        f'exit_status={failed_root.exit_status}, svg={failed_svg}'
    )


if __name__ == '__main__':
    main()
