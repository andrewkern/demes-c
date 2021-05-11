import subprocess
import tempfile
import pathlib

import pytest
import hypothesis as hyp
import hypothesis.strategies as st
import demes
import demes.hypothesis_strategies


@st.composite
def filtered_graphs(draw):
    graph = draw(demes.hypothesis_strategies.graphs())

    def is_ascii(s):
        return all(ord(c) < 128 for c in s)

    hyp.assume(all(is_ascii(deme.name) for deme in graph.demes))
    return graph


def resolve(filename: str) -> str:
    """
    Load a YAML file, resolve it using the C resolver, and return the
    fully-qualified YAML string.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outfile = pathlib.Path(tmpdir) / "out.yaml"
        subprocess.run(f"./resolve {filename} > {outfile}", shell=True, check=True)
        with open(outfile) as f:
            return f.read()


def compare_resolvers(graph1):
    with tempfile.TemporaryDirectory() as tmpdir:
        infile = pathlib.Path(tmpdir) / "in.yaml"
        demes.dump(graph1, infile)
        outstring = resolve(infile)
        graph2 = demes.loads(outstring)
        graph1.assert_close(graph2)


@hyp.settings(
    max_examples=1000,
    deadline=None,
    suppress_health_check=[hyp.HealthCheck.too_slow, hyp.HealthCheck.filter_too_much],
)
@hyp.given(filtered_graphs())
def test_random_graphs(graph):
    compare_resolvers(graph)


def example_files():
    example_dir = pathlib.Path("examples")
    files = list(example_dir.glob("**/*.yaml"))
    assert len(files) > 1
    return files


@pytest.mark.parametrize("filename", example_files())
def test_example_graphs(filename):
    graph = demes.load(filename)
    compare_resolvers(graph)
