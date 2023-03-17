from __future__ import annotations
import os
import logging
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
from copy import copy
from click.testing import CliRunner
from arcana.core.data.set import Dataset
from arcana.core.data.row import DataRow
from arcana.testing.data.blueprint import dataset_defaults, SIMPLE_DATASET
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

############
# CHANGEME #
############

TEST_STORE_URI = None  # os.environ["ARCANA_CHANGME_TEST_STORE_URI"]
TEST_STORE_USER = None  # os.environ["ARCANA_CHANGME_TEST_STORE_USER"]
TEST_STORE_PASSWORD = None  # os.environ["ARCANA_CHANGME_TEST_STORE_USER"]


def install_and_launch_app(
    name: str,
    command_config: dict,
    row: DataRow,
    inputs: dict[str, str],
    timeout: int = 1000,  # seconds
    poll_interval: int = 10,  # seconds
) -> tuple[int, str, str]:
    """Installs a new command to be run in the integrated workflow engine of the "changeme"
    data store, then launches it on the specified row with the provided inputs.

    Parameters
    ----------
    name : str
        The name to install the command as
    command_config : dict[str, Any]
        JSON that defines the XNAT command in the container service (see `generate_xnat_command`)
    row : DataRow
        the row of the dataset to run the app on
    inputs : dict[str, str]
        Inputs passed to the pipeline at launch (i.e. typically through text fields in the CS launch UI)
    timeout : int
        the time to wait for the pipeline to complete (seconds)
    poll_interval : int
        the time interval between status polls (seconds)

    Returns
    -------
    workflow_id : int
        the auto-generated ID for the launched workflow
    status : str
        the status of the completed workflow
    out_str : str
        stdout and stderr from the workflow run
    """
    raise NotImplementedError


# Change or remote this parameterisation if you only implement one of the data store templates
DATA_STORES = ["local", "remote"]


############
# FIXTURES #
############


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
    blueprint = copy(SIMPLE_DATASET)
    dataset_id, space, hierarchy = dataset_defaults(
        data_store, "simple", run_prefix, work_dir
    )
    blueprint.space = space
    blueprint.hierarchy = hierarchy
    blueprint.dim_lengths = [2 for _ in range(len(hierarchy))]
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
