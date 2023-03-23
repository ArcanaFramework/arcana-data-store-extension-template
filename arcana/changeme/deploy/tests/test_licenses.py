import pytest
from pathlib import Path
import docker
import docker.errors
from arcana.core.utils.misc import show_cli_trace
from arcana.core.cli.deploy import make_app, install_license
from arcana.testing.deploy.licenses import (
    get_pipeline_image,
    make_dataset,
    ORG,
    REGISTRY,
    IMAGE_VERSION,
    LICENSE_CONTENTS,
    LICENSE_NAME,
    LICENSE_INPUT_FIELD,
    LICENSE_OUTPUT_FIELD,
    LICENSE_PATH_PARAM,
    LICENSE_INPUT_PATH,
    LICENSE_OUTPUT_PATH,
)
from arcana.changeme.deploy import ExampleApp


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_site_runtime_license(license_file, work_dir, arcana_home, cli_runner):

    # build_dir = work_dir / "build"
    dataset_dir = work_dir / "dataset"

    LICENSE_PATH = work_dir / "license_location"

    pipeline_image = get_pipeline_image(LICENSE_PATH, app_cls=ExampleApp)

    # Save it into the new home directory
    dataset = make_dataset(dataset_dir)

    result = cli_runner(install_license, args=[LICENSE_NAME, str(license_file)])
    assert result.exit_code == 0, show_cli_trace(result)

    pipeline_image.command.execute(
        dataset.locator,
        input_values={LICENSE_INPUT_FIELD: LICENSE_INPUT_PATH},
        output_values={LICENSE_OUTPUT_FIELD: LICENSE_OUTPUT_PATH},
        parameter_values={LICENSE_PATH_PARAM: LICENSE_PATH},
        work_dir=work_dir / "pipeline",
        raise_errors=True,
        plugin="serial",
        loglevel="info",
    )


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_dataset_runtime_license(license_file, run_prefix, work_dir, cli_runner):

    # build_dir = work_dir / "build"
    dataset_dir = work_dir / "dataset"

    dataset = make_dataset(dataset_dir)

    LICENSE_PATH = work_dir / "license_location"
    pipeline_image = get_pipeline_image(LICENSE_PATH, app_cls=ExampleApp)

    result = cli_runner(
        install_license,
        args=[
            LICENSE_NAME,
            str(license_file),
            dataset.locator,
        ],
    )

    assert result.exit_code == 0, show_cli_trace(result)

    pipeline_image.command.execute(
        dataset.locator,
        input_values={LICENSE_INPUT_FIELD: LICENSE_INPUT_PATH},
        output_values={LICENSE_OUTPUT_FIELD: LICENSE_OUTPUT_PATH},
        parameter_values={LICENSE_PATH_PARAM: LICENSE_PATH},
        work_dir=work_dir / "pipeline",
        raise_errors=True,
        plugin="serial",
        loglevel="info",
    )


@pytest.fixture
def license_file(work_dir) -> Path:
    license_src = work_dir / "license_file.txt"

    with open(license_src, "w") as f:
        f.write(LICENSE_CONTENTS)

    return license_src
