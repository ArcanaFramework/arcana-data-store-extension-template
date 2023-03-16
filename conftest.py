from __future__ import annotations
import os
import logging
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
from click.testing import CliRunner
from fileformats.text import Plain as PlainText
from fileformats.field import Text as TextField
from arcana.testing.data.blueprint import (
    TestDatasetBlueprint,
    FileSetEntryBlueprint as FileBP,
    FieldEntryBlueprint as FieldBP,
)
from arcana.core.data.set import Dataset
from arcana.testing import TestDataSpace
from arcana.core.data.store import DataStore, LocalStore
from arcana.changeme.data import ExampleLocal, ExampleRemote
from pydra import set_input_validator

set_input_validator(True)

# Set DEBUG logging for unittests if required
log_level = logging.WARNING

logger = logging.getLogger("arcana")
logger.setLevel(log_level)

sch = logging.StreamHandler()
sch.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sch.setFormatter(formatter)
logger.addHandler(sch)


TEST_STORE_URI = None  # os.environ["ARCANA_CHANGME_TEST_STORE_URI"]
TEST_STORE_USER = None  # os.environ["ARCANA_CHANGME_TEST_STORE_USER"]
TEST_STORE_PASSWORD = None  # os.environ["ARCANA_CHANGME_TEST_STORE_USER"]

# Remove this parameterisation if you only implement one of the data store templates
DATA_STORES = ["local", "remote"]


@pytest.fixture(params=DATA_STORES)
def data_store(work_dir: Path, request):
    if request.param == "local":
        store = ExampleLocal()
    elif request.param == "remote":
        cache_dir = work_dir / "remote-cache"
        if None in (TEST_STORE_URI, TEST_STORE_USER, TEST_STORE_PASSWORD):
            raise NotImplementedError(
                "Need to set values of 'TEST_STORE_URI', 'TEST_STORE_USER' and "
                f"'TEST_STORE_PASSWORD' in {__file__} to point to a valid account on "
                "an instance of the remote store that can be used for testing, i.e. "
                "allow the creation of dummy test data.\n\n"
                "IT SHOULD NOT BE A PRODUCTION SERVER!!"
            )
        store = ExampleRemote(
            server=TEST_STORE_URI,
            cache_dir=cache_dir,
            user=TEST_STORE_USER,
            password=TEST_STORE_PASSWORD,
        )
        store.save("test_mock_store")
    else:
        assert False, f"Unrecognised store {request.param}"
    yield store


@pytest.fixture
def simple_dataset(data_store, work_dir, run_prefix) -> Dataset:
    dataset_id, space, hierarchy = dataset_defaults(
        data_store, "simple", run_prefix, work_dir
    )
    blueprint = TestDatasetBlueprint(  # dataset name
        space=space,
        hierarchy=hierarchy,
        dim_lengths=[2 for _ in range(len(hierarchy))],
        entries=[
            FileBP(path="file1", datatype=PlainText, filenames=["file.txt"]),
            FieldBP(path="field1", datatype=TextField, value="a field"),
        ],
    )
    return blueprint.make_dataset(data_store, dataset_id, name="")


@pytest.fixture(scope="session")
def run_prefix():
    "A datetime string used to avoid stale data left over from previous tests"
    return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")


@pytest.fixture
def cli_runner(catch_cli_exceptions):
    def invoke(*args, catch_exceptions=catch_cli_exceptions, **kwargs):
        runner = CliRunner()
        result = runner.invoke(*args, catch_exceptions=catch_exceptions, **kwargs)
        return result

    return invoke


@pytest.fixture
def work_dir() -> Path:
    work_dir = tempfile.mkdtemp()
    return Path(work_dir)


# For debugging in IDE's don't catch raised exceptions and let the IDE
# break at it
if os.getenv("_PYTEST_RAISE", "0") != "0":

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value

    CATCH_CLI_EXCEPTIONS = False
else:
    CATCH_CLI_EXCEPTIONS = True


@pytest.fixture
def catch_cli_exceptions():
    return CATCH_CLI_EXCEPTIONS


def dataset_defaults(
    data_store: DataStore, dataset_name: str, run_prefix: str, work_dir: Path
) -> tuple[str, type, list[str]]:
    """Return sensible defaults for the dataset ID, data-space and hierarchy for
    datasets created in the given data store

    Parameters
    ----------
    data_store : DataStore
        the data store to get the defaults for
    dataset_name : str
        the name of the dataset in the test matrix

    Returns
    -------
    dataset_id : str
        the ID for the test dataset
    space : type
        the data-space for the dataset
    hierarchy : list[str]
        the default hierarchy for the given data store
    """
    try:
        space = data_store.DEFAULT_SPACE
    except AttributeError:
        space = TestDataSpace
    try:
        hierarchy = data_store.DEFAULT_HIERARCHY
    except AttributeError:
        hierarchy = [str(h) for h in max(space).span()]
    if isinstance(data_store.name, LocalStore):
        dataset_id = work_dir / dataset_name
    else:
        dataset_id = dataset_name
    return run_prefix + dataset_id, space, hierarchy
