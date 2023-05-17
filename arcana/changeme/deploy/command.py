from __future__ import annotations
import typing as ty
import attrs
from arcana.core.deploy.command.base import ContainerCommand

if ty.TYPE_CHECKING:
    from .app import ExampleApp


@attrs.define(kw_only=True)
class ExampleCommand(ContainerCommand):

    image: ty.Optional[ExampleApp] = None

    # Hard-code the data_space of XNAT commands to be clinical
    # DATA_SPACE = Clinical

    def make_config(self):
        """Constructs a configuration from the command attributes

        Returns
        -------
        dict
            returns a configuration dictionary, which could be installed in the
            data store to enable the command to be called
        """

        config = self.init_config()

        input_args = self.add_input_fields(config)

        param_args = self.add_parameter_fields(config)

        output_args = self.add_output_fields(config)

        flag_arg = self.add_arcana_flags_field(config)

        config["command-line"] = (
            self.activate_conda_cmd()
            + "arcana ext xnat cs-entrypoint xnat-cs//[PROJECT_ID] "
            + " ".join(input_args + output_args + param_args + [flag_arg])
        )

        return config

    def init_config(self):
        """Initialises the configuration dictionary

        Returns
        -------
        dict[str, *]
            the JSON-like dictionary to specify the command to the XNAT CS
        """
        raise NotImplementedError

    def add_input_fields(self, config):
        """Adds pipeline inputs to the configuration

        Parameters
        ----------
        config : dict
            JSON-like dictionary to be passed to the data store to let it know how to
            run the command

        Returns
        -------
        list[str]
            list of arguments to be appended to the command line
        """
        raise NotImplementedError

    def add_parameter_fields(self, config):
        """Adds pipeline inputs to the configuration

        Parameters
        ----------
        config : dict
            JSON-like dictionary to be passed to the data store to let it know how to
            run the command

        Returns
        -------
        list[str]
            list of arguments to be appended to the command line
        """
        raise NotImplementedError

    def add_output_fields(self, config):
        """Adds pipeline inputs to the configuration

        Parameters
        ----------
        config : dict
            JSON-like dictionary to be passed to the data store to let it know how to
            run the command

        Returns
        -------
        list[str]
            list of arguments to be appended to the command line
        """
        raise NotImplementedError

    def add_arcana_flags_field(self, config):
        """Adds pipeline inputs to the configuration

        Parameters
        ----------
        config : dict
            JSON-like dictionary to be passed to the data store to let it know how to
            run the command

        Returns
        -------
        list[str]
            list of arguments to be appended to the command line
        """
        raise NotImplementedError
