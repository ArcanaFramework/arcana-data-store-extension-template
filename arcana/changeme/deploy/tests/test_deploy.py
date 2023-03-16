from pathlib import Path
import pytest
from arcana.changeme.deploy import ExampleApp
from arcana.core.data.set import Dataset
from arcana.testing.data.blueprint import (
    TestDatasetBlueprint,
    FileSetEntryBlueprint as FileBP,
)
from fileformats.text import Plain as PlainText
from conftest import install_and_launch_app, dataset_defaults


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_app(concatenate_dataset: Dataset, build_spec: dict, work_dir: Path):
    """Tests the complete "changeme" deployment pipeline by building and running an app
    against a test dataset"""

    image_spec = ExampleApp(**build_spec)

    image_spec.make(
        build_dir=work_dir / "app-build",
        arcana_install_extras=["test"],
        use_local_packages=True,
        use_test_config=True,
    )

    with concatenate_dataset.data_store.connection:

        row = next(iter(concatenate_dataset.rows()))

        workflow_id, status, out_str = install_and_launch_app(
            command_config=image_spec.command.make_config(),
            row=row,
            inputs={
                "first_file": "file1",
                "second_file": "file2",
                "number_of_duplicates": 2,
            },
        )

        # assert status == "complete", f"workflow ({workflow_id}) didn't complete successfully: {status}\n\n{out_str}"
        assert row["concatenated"].contents == "file1.txt\nfile2.txt\nfile1.txt\nfile2.txt"


@pytest.fixture
def concatenate_dataset(data_store, work_dir, run_prefix) -> Dataset:
    dataset_id, space, hierarchy = dataset_defaults(
        data_store, "concatenate", run_prefix, work_dir
    )
    blueprint = TestDatasetBlueprint(
        space=space,
        hierarchy=hierarchy,
        dim_lengths=[1 for _ in range(len(hierarchy))],
        entries=[
            FileBP(path="file1", datatype=PlainText, filenames=["file1.txt"]),
            FileBP(path="file2", datatype=PlainText, filenames=["file2.txt"]),
        ],
    )
    return blueprint.make_dataset(data_store, dataset_id, name="")


@pytest.fixture
def build_spec(run_prefix):
    return {
        "org": "arcana-tests",
        "name": "concatenate-app" + run_prefix,
        "version": "1.0",
        "description": "A pipeline to test deployment to changme data stores",
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
        "command": {
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
        },
    }
