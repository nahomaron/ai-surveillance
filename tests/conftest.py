import pytest

from rq1.fixtures import clips


@pytest.fixture(scope="session")
def clip_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("s1clips")
    clips.build_all(out)
    return out
