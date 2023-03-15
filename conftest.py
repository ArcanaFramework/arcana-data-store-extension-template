import os
import logging
import pytest

# Set DEBUG logging for unittests

log_level = logging.WARNING

logger = logging.getLogger("arcana")
logger.setLevel(log_level)

sch = logging.StreamHandler()
sch.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sch.setFormatter(formatter)
logger.addHandler(sch)


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



import os
import logging
import sys
from tempfile import mkdtemp
from unittest.mock import patch
import json
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
import numpy
import docker
import random
import nibabel
from click.testing import CliRunner
from imageio.core.fetching import get_remote_file
import xnat4tests
import medimages4tests.dummy.nifti
import medimages4tests.dummy.dicom.mri.fmap.siemens.skyra.syngo_d13c
from arcana.core.deploy.image.base import BaseImage
from arcana.core.data import Clinical
from fileformats.medimage import NiftiGzX, NiftiGz, DicomSet, NiftiX
from fileformats.text import Plain as Text
from fileformats.image import Png
from fileformats.serialization import Json
from fileformats.generic import Directory
from arcana.xnat.data.api import Xnat
from arcana.xnat.utils.testing import (
    TestXnatDatasetBlueprint,
    FileSetEntryBlueprint as FileBP,
    ScanBlueprint as ScanBP,
)
from arcana.xnat.data.cs import XnatViaCS
from pydra import set_input_validator

set_input_validator(True)


PKG_DIR = Path(__file__).parent


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





@pytest.fixture(scope="session")
def build_cache_dir():
    return Path(mkdtemp())


@pytest.fixture(scope="session")
def pkg_dir():
    return PKG_DIR


@pytest.fixture
def arcana_home(work_dir):
    arcana_home = work_dir / "arcana-home"
    with patch.dict(os.environ, {"ARCANA_HOME": str(arcana_home)}):
        yield arcana_home


# -----------------------
# Test dataset structures
# -----------------------


TEST_XNAT_DATASET_BLUEPRINTS = {
    "basic": TestXnatDatasetBlueprint(  # dataset name
        dim_lengths=[1, 1, 3],  # number of timepoints, groups and members respectively
        scans=[
            ScanBP(
                name="scan1",  # scan type (ID is index)
                resources=[
                    FileBP(
                        path="Text",
                        datatype=Text,
                        filenames=["file.txt"],  # resource name  # Data datatype
                    )
                ],
            ),  # name files to place within resource
            ScanBP(
                name="scan2",
                resources=[
                    FileBP(
                        path="NiftiGzX",
                        datatype=NiftiGzX,
                        filenames=["nifti/anat/T1w.nii.gz", "nifti/anat/T1w.json"],
                    )
                ],
            ),
            ScanBP(
                name="scan3",
                resources=[
                    FileBP(
                        path="Directory",
                        datatype=Directory,
                        filenames=["doubledir"],
                    )
                ],
            ),
            ScanBP(
                name="scan4",
                resources=[
                    FileBP(
                        path="DICOM",
                        datatype=DicomSet,
                        filenames=[
                            "dicom/fmap/1.dcm",
                            "dicom/fmap/2.dcm",
                            "dicom/fmap/3.dcm",
                        ],
                    ),
                    FileBP(
                        path="NIFTI",
                        datatype=NiftiGz,
                        filenames=["nifti/anat/T2w.nii.gz"],
                    ),
                    FileBP(
                        path="BIDS", datatype=Json, filenames=["nifti/anat/T2w.json"]
                    ),
                    FileBP(
                        path="SNAPSHOT", datatype=Png, filenames=["images/chelsea.png"]
                    ),
                ],
            ),
        ],
        derivatives=[
            FileBP(
                path="deriv1",
                row_frequency=Clinical.timepoint,
                datatype=Text,
                filenames=["file.txt"],
            ),
            FileBP(
                path="deriv2",
                row_frequency=Clinical.subject,
                datatype=NiftiGzX,
                filenames=["nifti/anat/T1w.nii.gz", "nifti/anat/T1w.json"],
            ),
            FileBP(
                path="deriv3",
                row_frequency=Clinical.batch,
                datatype=Directory,
                filenames=["dir"],
            ),
            FileBP(
                path="deriv4",
                row_frequency=Clinical.dataset,
                datatype=Text,
                filenames=["file.txt"],
            ),
        ],
    ),  # id_composition dict
    "multi": TestXnatDatasetBlueprint(  # dataset name
        dim_lengths=[2, 2, 2],  # number of timepoints, groups and members respectively
        scans=[
            ScanBP(
                name="scan1",
                resources=[FileBP(path="Text", datatype=Text, filenames=["file.txt"])],
            )
        ],
        id_composition={
            "subject": r"group(?P<group>\d+)member(?P<member>\d+)",
            "session": r"timepoint(?P<timepoint>\d+).*",
        },  # id_composition dict
        derivatives=[
            FileBP(
                path="deriv1",
                row_frequency=Clinical.session,
                datatype=Text,
                filenames=["file.txt"],
            ),
            FileBP(
                path="deriv2",
                row_frequency=Clinical.subject,
                datatype=NiftiGzX,
                filenames=["nifti/anat/T2w.nii.gz", "nifti/anat/T2w.json"],
            ),
            FileBP(
                path="deriv3",
                row_frequency=Clinical.timepoint,
                datatype=Directory,
                filenames=["doubledir"],
            ),
            FileBP(
                path="deriv4",
                row_frequency=Clinical.member,
                datatype=Text,
                filenames=["file.txt"],
            ),
            FileBP(
                path="deriv5",
                row_frequency=Clinical.dataset,
                datatype=Text,
                filenames=["file.txt"],
            ),
            FileBP(
                path="deriv6",
                row_frequency=Clinical.batch,
                datatype=Text,
                filenames=["file.txt"],
            ),
            FileBP(
                path="deriv7",
                row_frequency=Clinical.matchedpoint,
                datatype=Text,
                filenames=["file.txt"],
            ),
            FileBP(
                path="deriv8",
                row_frequency=Clinical.group,
                datatype=Text,
                filenames=["file.txt"],
            ),
        ],
    ),
    "concatenate_test": TestXnatDatasetBlueprint(
        dim_lengths=[1, 1, 2],
        scans=[
            ScanBP(
                name="scan1",
                resources=[FileBP(path="Text", datatype=Text, filenames=["file1.txt"])],
            ),
            ScanBP(
                name="scan2",
                resources=[FileBP(path="Text", datatype=Text, filenames=["file2.txt"])],
            ),
        ],
        derivatives=[
            FileBP(
                path="concatenated",
                row_frequency=Clinical.session,
                datatype=Text,
                filenames=["concatenated.txt"],
            )
        ],
    ),
}

GOOD_DATASETS = ["basic.api", "multi.api", "basic.cs", "multi.cs"]
MUTABLE_DATASETS = ["basic.api", "multi.api", "basic.cs", "multi.cs"]

# ------------------------------------
# Pytest fixtures and helper functions
# ------------------------------------


@pytest.fixture(params=GOOD_DATASETS, scope="session")
def xnat_dataset(
    xnat_repository: Xnat,
    xnat_archive_dir: Path,
    source_data: Path,
    run_prefix: str,
    request,
):
    dataset_id, access_method = request.param.split(".")
    blueprint = TEST_XNAT_DATASET_BLUEPRINTS[dataset_id]
    project_id = run_prefix + dataset_id
    with xnat4tests.connect() as login:
        if project_id not in login.projects:
            blueprint.make_dataset(
                dataset_id=project_id, store=xnat_repository, source_data=source_data
            )
            logger.info("Creating read-only project at %s", project_id)
        else:
            logger.info(
                "Accessing previously created read-only project at %s", project_id
            )
    store = get_test_repo(project_id, access_method, xnat_repository, xnat_archive_dir)
    return blueprint.access_dataset(
        dataset_id=project_id,
        store=store,
    )


@pytest.fixture(params=MUTABLE_DATASETS, scope="function")
def mutable_dataset(
    xnat_repository: Xnat,
    xnat_archive_dir: Path,
    source_data: Path,
    run_prefix: str,
    request,
):
    dataset_id, access_method = request.param.split(".")
    blueprint = TEST_XNAT_DATASET_BLUEPRINTS[dataset_id]
    project_id = (
        run_prefix
        + dataset_id
        + "mutable"
        + access_method
        + str(hex(random.getrandbits(16)))[2:]
    )
    store = get_test_repo(project_id, access_method, xnat_repository, xnat_archive_dir)
    return blueprint.make_dataset(
        store=store,
        dataset_id=project_id,
        source_data=source_data,
    )


@pytest.fixture
def simple_dataset(xnat_repository, work_dir, run_prefix):
    blueprint = TestXnatDatasetBlueprint(
        dim_lengths=[1, 1, 1],
        scans=[
            ScanBP(
                name="scan1",
                resources=[FileBP(path="TEXT", datatype=Text, filenames=["file.txt"])])
        ],
    )
    project_id = (
        run_prefix
        + "simple"
        + str(hex(random.getrandbits(16)))[2:]
    )
    return blueprint.make_dataset(xnat_repository, project_id, name="")


def get_test_repo(
    project_id: str,
    access_method: str,
    xnat_repository: Xnat,
    xnat_archive_dir: Path,
):
    if access_method == "cs":
        proj_dir = xnat_archive_dir / project_id / "arc001"
        store = XnatViaCS(
            server=xnat_repository.server,
            user=xnat_repository.user,
            password=xnat_repository.password,
            cache_dir=xnat_repository.cache_dir,
            row_frequency=Clinical.dataset,
            input_mount=proj_dir,
            output_mount=Path(mkdtemp()),
        )
    elif access_method == "api":
        store = xnat_repository
    else:
        assert False, f"unrecognised access method {access_method}"
    return store


@pytest.fixture(scope="session")
def xnat4tests_config() -> xnat4tests.Config:

    return xnat4tests.Config()


@pytest.fixture(scope="session")
def xnat_root_dir(xnat4tests_config) -> Path:
    return xnat4tests_config.xnat_root_dir


@pytest.fixture(scope="session")
def xnat_archive_dir(xnat_root_dir):
    return xnat_root_dir / "archive"


@pytest.fixture(scope="session")
def xnat_repository(run_prefix, xnat4tests_config):

    xnat4tests.start_xnat()

    repository = Xnat(
        server=xnat4tests_config.xnat_uri,
        user=xnat4tests_config.xnat_user,
        password=xnat4tests_config.xnat_password,
        cache_dir=mkdtemp(),
    )

    # Stash a project prefix in the repository object
    repository.__annotations__["run_prefix"] = run_prefix

    yield repository


@pytest.fixture(scope="session")
def xnat_via_cs_repository(run_prefix, xnat4tests_config):

    xnat4tests.start_xnat()

    repository = Xnat(
        server=xnat4tests_config.xnat_uri,
        user=xnat4tests_config.xnat_user,
        password=xnat4tests_config.xnat_password,
        cache_dir=mkdtemp(),
    )

    # Stash a project prefix in the repository object
    repository.__annotations__["run_prefix"] = run_prefix

    yield repository


@pytest.fixture(scope="session")
def xnat_respository_uri(xnat_repository):
    return xnat_repository.server


@pytest.fixture(scope="session")
def docker_registry_for_xnat():
    return xnat4tests.start_registry()


@pytest.fixture(scope="session")
def docker_registry_for_xnat_uri(docker_registry_for_xnat):
    if sys.platform == "linux":
        uri = "172.17.0.1"  # Linux + GH Actions
    else:
        uri = "host.docker.internal"  # Mac/Windows local debug
    return uri


@pytest.fixture
def dummy_niftix(work_dir):

    nifti_path = work_dir / "t1w.nii"
    json_path = work_dir / "t1w.json"

    # Create a random Nifti file to satisfy BIDS parsers
    hdr = nibabel.Nifti1Header()
    hdr.set_data_shape((10, 10, 10))
    hdr.set_zooms((1.0, 1.0, 1.0))  # set voxel size
    hdr.set_xyzt_units(2)  # millimeters
    hdr.set_qform(numpy.diag([1, 2, 3, 1]))
    nibabel.save(
        nibabel.Nifti1Image(
            numpy.random.randint(0, 1, size=[10, 10, 10]),
            hdr.get_best_affine(),
            header=hdr,
        ),
        nifti_path,
    )

    with open(json_path, "w") as f:
        json.dump({"test": "json-file"}, f)

    return NiftiX.from_fspaths(nifti_path, json_path)


@pytest.fixture(scope="session")
def command_spec():
    return {
        "task": "arcana.testing.tasks:concatenate",
        "inputs": {
            "first_file": {
                "datatype": "fileformats.text:Plain",
                "field": "in_file1",
                "default_column": {
                    "row_frequency": "session",
                },
                "help_string": "the first file to pass as an input",
            },
            "second_file": {
                "datatype": "fileformats.text:Plain",
                "field": "in_file2",
                "default_column": {
                    "row_frequency": "session",
                },
                "help_string": "the second file to pass as an input",
            },
        },
        "outputs": {
            "concatenated": {
                "datatype": "fileformats.text:Plain",
                "field": "out_file",
                "help_string": "an output file",
            }
        },
        "parameters": {
            "number_of_duplicates": {
                "field": "duplicates",
                "default": 2,
                "datatype": "int",
                "required": True,
                "help_string": "a parameter",
            }
        },
        "row_frequency": "session",
    }


BIDS_VALIDATOR_DOCKER = "bids/validator:latest"
SUCCESS_STR = "This dataset appears to be BIDS compatible"
MOCK_BIDS_APP_IMAGE = "arcana-mock-bids-app"
BIDS_VALIDATOR_APP_IMAGE = "arcana-bids-validator-app"


@pytest.fixture(scope="session")
def bids_command_spec(mock_bids_app_executable):
    inputs = {
        "T1w": {
            "configuration": {
                "path": "anat/T1w",
            },
            "datatype": "fileformats.medimage:NiftiGzX",
            "help_string": "T1-weighted image",
        },
        "T2w": {
            "configuration": {
                "path": "anat/T2w",
            },
            "datatype": "fileformats.medimage:NiftiGzX",
            "help_string": "T2-weighted image",
        },
        "DWI": {
            "configuration": {
                "path": "dwi/dwi",
            },
            "datatype": "fileformats.medimage:NiftiGzXBvec",
            "help_string": "DWI-weighted image",
        },
    }

    outputs = {
        "file1": {
            "configuration": {
                "path": "file1",
            },
            "datatype": "fileformats.text:Plain",
            "help_string": "an output file",
        },
        "file2": {
            "configuration": {
                "path": "file2",
            },
            "datatype": "fileformats.text:Plain",
            "help_string": "another output file",
        },
    }

    return {
        "task": "arcana.bids.tasks:bids_app",
        "inputs": inputs,
        "outputs": outputs,
        "row_frequency": "session",
        "configuration": {
            "inputs": inputs,
            "outputs": outputs,
            "executable": str(mock_bids_app_executable),
        },
    }


@pytest.fixture(scope="session")
def bids_success_str():
    return SUCCESS_STR


@pytest.fixture(scope="session")
def bids_validator_app_script():
    return f"""#!/bin/sh
# Echo inputs to get rid of any quotes
BIDS_DATASET=$(echo $1)
OUTPUTS_DIR=$(echo $2)
SUBJ_ID=$5
# Run BIDS validator to check whether BIDS dataset is created properly
output=$(/usr/local/bin/bids-validator "$BIDS_DATASET")
if [[ "$output" != *"{SUCCESS_STR}"* ]]; then
    echo "BIDS validation was not successful, exiting:\n "
    echo $output
    exit 1;
fi
# Write mock output files to 'derivatives' Directory
mkdir -p $OUTPUTS_DIR
echo 'file1' > $OUTPUTS_DIR/sub-${{SUBJ_ID}}_file1.txt
echo 'file2' > $OUTPUTS_DIR/sub-${{SUBJ_ID}}_file2.txt
"""


# FIXME: should be converted to python script to be Windows compatible
@pytest.fixture(scope="session")
def mock_bids_app_script():
    file_tests = ""
    for inpt_path, datatype in [
        ("anat/T1w", NiftiGzX),
        ("anat/T2w", NiftiGzX),
        ("dwi/dwi", NiftiGzX),
    ]:
        subdir, suffix = inpt_path.split("/")
        file_tests += f"""
        if [ ! -f "$BIDS_DATASET/sub-${{SUBJ_ID}}/{subdir}/sub-${{SUBJ_ID}}_{suffix}{datatype.ext}" ]; then
            echo "Did not find {suffix} file at $BIDS_DATASET/sub-${{SUBJ_ID}}/{subdir}/sub-${{SUBJ_ID}}_{suffix}{datatype.ext}"
            exit 1;
        fi
        """

    return f"""#!/bin/sh
BIDS_DATASET=$1
OUTPUTS_DIR=$2
SUBJ_ID=$5
{file_tests}
# Write mock output files to 'derivatives' Directory
mkdir -p $OUTPUTS_DIR
echo 'file1' > $OUTPUTS_DIR/sub-${{SUBJ_ID}}_file1.txt
echo 'file2' > $OUTPUTS_DIR/sub-${{SUBJ_ID}}_file2.txt
"""


@pytest.fixture(scope="session")
def mock_bids_app_executable(build_cache_dir, mock_bids_app_script):
    # Create executable that runs validator then produces some mock output
    # files
    script_path = build_cache_dir / "mock-bids-app-executable.sh"
    with open(script_path, "w") as f:
        f.write(mock_bids_app_script)
    os.chmod(script_path, 0o777)
    return script_path


@pytest.fixture(scope="session")
def mock_bids_app_image(mock_bids_app_script, build_cache_dir):
    return build_app_image(
        MOCK_BIDS_APP_IMAGE,
        mock_bids_app_script,
        build_cache_dir,
        base_image=BaseImage().reference,
    )


def build_app_image(tag_name, script, build_cache_dir, base_image):
    dc = docker.from_env()

    # Create executable that runs validator then produces some mock output
    # files
    build_dir = build_cache_dir / tag_name.replace(":", "__i__")
    build_dir.mkdir()
    launch_sh = build_dir / "launch.sh"
    with open(launch_sh, "w") as f:
        f.write(script)

    # Build mock BIDS app image
    with open(build_dir / "Dockerfile", "w") as f:
        f.write(
            f"""FROM {base_image}
ADD ./launch.sh /launch.sh
RUN chmod +x /launch.sh
ENTRYPOINT ["/launch.sh"]"""
        )

    dc.images.build(path=str(build_dir), tag=tag_name)

    return tag_name


@pytest.fixture(scope="session")
def source_data():
    source_data = Path(tempfile.mkdtemp())
    # Create NIFTI data
    nifti_dir = source_data / "nifti"
    nifti_dir.mkdir()
    for fname, fdata in NIFTI_DATA_SPEC.items():
        fpath = nifti_dir.joinpath(*fname.split("/"))
        fpath.parent.mkdir(exist_ok=True, parents=True)
        if fname.endswith(".nii.gz") or fname.endswith(".nii"):
            medimages4tests.dummy.nifti.get_image(out_file=fpath)
        elif fname.endswith(".json"):
            with open(fpath, "w") as f:
                json.dump(fdata, f)
        else:
            with open(fpath, "w") as f:
                f.write(fdata)
    # Create DICOM data
    dicom_dir = source_data / "dicom"
    dicom_dir.mkdir()
    medimages4tests.dummy.dicom.mri.fmap.siemens.skyra.syngo_d13c.get_image(
        out_dir=dicom_dir / "fmap"
    )
    # Create png data
    get_remote_file("images/chelsea.png", directory=source_data)
    return source_data


@pytest.fixture(scope="session")
def nifti_sample_dir(source_data):
    return source_data / "nifti"