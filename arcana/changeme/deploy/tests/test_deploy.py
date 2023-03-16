from tempfile import mkdtemp
from pathlib import Path
import pytest
from conftest import (
    TEST_XNAT_DATASET_BLUEPRINTS,
    TestXnatDatasetBlueprint,
    ScanBP,
    FileBP,
    get_test_repo,
)
from fileformats.medimage import NiftiGzX, NiftiGzXBvec
from arcana.changeme.deploy import ExampleApp
from arcana.core.data.set import Dataset
from conftest import install_and_launch_app



@pytest.fixture(scope="session")
def build_cache_dir():
    return Path(mkdtemp())


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


PIPELINE_NAME = "test-concatenate"


@pytest.fixture(params=["func", "bids_app"], scope="session")
def run_spec(
    command_spec,
    bids_command_spec,
    xnat_repository,
    xnat_archive_dir,
    request,
    nifti_sample_dir,
    mock_bids_app_image,
    run_prefix,
):
    spec = {}
    if request.param == "func":
        spec["build"] = {
            "org": "arcana-tests",
            "name": "concatenate-xnat-cs",
            "version": "1.0",
            "description": "A pipeline to test Arcana's deployment tool",
            "command": command_spec,
            "authors": [{"name": "Some One", "email": "some.one@an.email.org"}],
            "info_url": "http://concatenate.readthefakedocs.io",
            "readme": "This is a test README",
            "registry": "a.docker.registry.io",
            "packages": {
                "system": ["git", "vim"],
                "pip": [
                    "arcana",
                    "arcana-xnat",
                    "fileformats",
                    "fileformats-medimage",
                    "pydra",
                ],
            },
        }
        blueprint = TEST_XNAT_DATASET_BLUEPRINTS["concatenate_test"]
        project_id = run_prefix + "concatenate_test"
        store = get_test_repo(project_id, "cs", xnat_repository, xnat_archive_dir)
        spec["dataset"] = blueprint.make_dataset(
            store=store,
            dataset_id=project_id,
        )
        spec["params"] = {"duplicates": 2}
    elif request.param == "bids_app":
        bids_command_spec["configuration"]["executable"] = "/launch.sh"
        spec["build"] = {
            "org": "arcana-tests",
            "name": "bids-app-xnat-cs",
            "version": "1.0",
            "description": "A pipeline to test wrapping of BIDS apps",
            "base_image": {
                "name": mock_bids_app_image,
                "package_manager": "apt",
            },
            "packages": {
                "system": ["git", "vim"],
                "pip": [
                    "arcana",
                    "arcana-xnat",
                    "arcana-bids",
                    "fileformats",
                    "fileformats-medimage",
                    "pydra",
                ],
            },
            "command": bids_command_spec,
            "authors": [
                {"name": "Some One Else", "email": "some.oneelse@an.email.org"}
            ],
            "info_url": "http://a-bids-app.readthefakedocs.io",
            "readme": "This is another test README for BIDS app image",
            "registry": "another.docker.registry.io",
        }
        blueprint = TestXnatDatasetBlueprint(
            dim_lengths=[1, 1, 1],
            scans=[
                ScanBP(
                    "anat/T1w",
                    [
                        FileBP(
                            path="NiftiGzX",
                            datatype=NiftiGzX,
                            filenames=["anat/T1w.nii.gz", "anat/T1w.json"],
                        )
                    ],
                ),
                ScanBP(
                    "anat/T2w",
                    [
                        FileBP(
                            path="NiftiGzX",
                            datatype=NiftiGzX,
                            filenames=["anat/T2w.nii.gz", "anat/T2w.json"],
                        )
                    ],
                ),
                ScanBP(
                    "dwi/dwi",
                    [
                        FileBP(
                            path="NiftiGzXBvec",
                            datatype=NiftiGzXBvec,
                            filenames=[
                                "dwi/dwi.nii.gz",
                                "dwi/dwi.json",
                                "dwi/dwi.bvec",
                                "dwi/dwi.bval",
                            ],
                        )
                    ],
                ),
            ],
        )
        project_id = run_prefix + "xnat_cs_bids_app"
        store = get_test_repo(project_id, "cs", xnat_repository, xnat_archive_dir)
        spec["dataset"] = blueprint.make_dataset(
            store=store,
            dataset_id=project_id,
            source_data=nifti_sample_dir,
        )
        spec["params"] = {}
    else:
        assert False, f"unrecognised request param '{request.param}'"
    return spec


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_app(simple_dataset: Dataset, run_spec, command_spec, run_prefix, work_dir: Path):
    """Tests the complete XNAT deployment pipeline by building and running a
    container"""

    # Retrieve test dataset and build and command specs from fixtures
    build_spec = run_spec["build"]
    dataset = run_spec["dataset"]
    params = run_spec["params"]
    blueprint = dataset.__annotations__["blueprint"]

    # Append run_prefix to command name to avoid clash with previous test runs
    build_spec["name"] = "app-test" + run_prefix

    image_spec = ExampleApp(**build_spec)

    image_spec.make(
        build_dir=work_dir,
        arcana_install_extras=["test"],
        use_local_packages=True,
        use_test_config=True,
    )

    launch_inputs = {}

    for inpt, scan in zip(command_spec["inputs"], blueprint.scans):
        launch_inputs[inpt["name"]] = scan.name

    for pname, pval in params.items():
        launch_inputs[pname] = pval

    with simple_dataset.data_store.connection:

        row = next(iter(simple_dataset.rows()))

        workflow_id, status, out_str = install_and_launch_app(
            command_config=image_spec.command.make_config(),
            row=row,
            inputs=launch_inputs,
        )

        # assert status == "Complete", f"Workflow {workflow_id} failed.\n{out_str}"
