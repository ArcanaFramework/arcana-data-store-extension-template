import click
from arcana.core.deploy.command import entrypoint_opts
from arcana.changeme.deploy import ExampleApp
from arcana.core.cli.ext import ext


@ext.group(
    name="changeme",
    help="CLI extensions for interacting with BIDS datasets"
)
def changeme_group():
    pass


@changeme_group.command(
    name="app-entrypoint",
    help="""Loads a dataset, or creates one it is not already present, then applies and
launches a pipeline in a single command.

DATASET_LOCATOR string containing the nickname of the data store, the ID of the
dataset (e.g. XNAT project ID or file-system directory) and the dataset's name
in the format <store-nickname>//<dataset-id>[@<dataset-name>]

""",
)
@click.argument("dataset_locator")
@entrypoint_opts.parameterisation
@entrypoint_opts.execution
@entrypoint_opts.debugging
@entrypoint_opts.dataset_config
def app_entrypoint(
    dataset_locator,
    spec_path,
    **kwargs,
):

    image_spec = ExampleApp.load(spec_path)

    image_spec.command.execute(
        dataset_locator,
        **kwargs,
    )
