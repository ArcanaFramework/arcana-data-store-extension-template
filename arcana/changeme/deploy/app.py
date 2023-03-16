from __future__ import annotations
from pathlib import Path
import shlex
import attrs
from neurodocker.reproenv import DockerRenderer
from arcana.core.deploy.image import App
from arcana.core.utils.serialize import (
    ObjectConverter,

)
from .command import ExampleCommand


@attrs.define(kw_only=True)
class ExampleApp(App):

    command: ExampleCommand = attrs.field(converter=ObjectConverter(ExampleCommand))

    def add_entrypoint(self, dockerfile: DockerRenderer, build_dir: Path):

        command_line = (
            self.command.activate_conda_cmd() + "arcana ext changeme app-entrypoint"
        )

        dockerfile.entrypoint(shlex.split(command_line))
