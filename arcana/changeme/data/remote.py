from __future__ import annotations
import typing as ty
from pathlib import Path
import attrs
from fileformats.core.base import FileSet
from arcana.core.data.store import RemoteStore
from arcana.core.data.row import DataRow
from arcana.core.data.tree import DataTree
from arcana.core.data.entry import DataEntry


@attrs.define(kw_only=True, slots=False)
class ExampleRemote(RemoteStore):
    """An example data-store that connects to a remote store. Please see the Attrs
    documentation (https://www.attrs.org/en/stable/) for instructions on how to
    design Python classes using the `attrs` package.

    Parameters
    ----------
    """

    #############################
    # DataStore abstractmethods #
    #############################

    def populate_tree(self, tree: DataTree):
        """
        Find all data rows for a dataset in the store and populate the
        Dataset object using its `add_leaf` method.

        Parameters
        ----------
        dataset : Dataset
            The dataset to populate with rows
        """
        raise NotImplementedError

    def populate_row(self, row: DataRow):
        """
        Find all data items within a data row and populate the DataRow object
        with them using the `add_fileset` and `add_field` methods.

        Parameters
        ----------
        row : DataRow
            The data row to populate with items
        """
        raise NotImplementedError

    def save_dataset_definition(
        self, dataset_id: str, definition: dict[str, ty.Any], name: str
    ):
        """Save definition of dataset within the store

        Parameters
        ----------
        dataset_id: str
            The ID/path of the dataset within the store
        definition: dict[str, Any]
            A dictionary containing the dct Dataset to be saved. The
            dictionary is in a format ready to be dumped to file as JSON or
            YAML.
        name: str
            Name for the dataset definition to distinguish it from other
            definitions for the same directory/project"""
        raise NotImplementedError

    def load_dataset_definition(self, dataset_id: str, name: str) -> dict[str, ty.Any]:
        """Load definition of a dataset saved within the store

        Parameters
        ----------
        dataset_id: str
            The ID (e.g. file-system path, XNAT project ID) of the project
        name: str
            Name for the dataset definition to distinguish it from other
            definitions for the same directory/project

        Returns
        -------
        definition: dict[str, Any]
            A dct Dataset object that was saved in the data store
        """
        raise NotImplementedError

    def connect(self):
        """
        If a connection session is required to the store manage it here

        Parameters
        ----------
        session : Any
            the session object returned by `connect` to be closed gracefully
        """
        raise NotImplementedError

    def disconnect(self, session):
        """
        If a connection session is required to the store manage it here

        Parameters
        ----------
        session : Any
            the session object returned by `connect` to be closed gracefully
        """
        raise NotImplementedError

    def get_provenance(self, entry: DataEntry) -> dict[str, ty.Any]:
        """Retrieves provenance information for a given data entry in the store

        Parameters
        ----------
        entry: DataEntry
            The entry to retrieve the provenance data for

        Returns
        -------
        provenance: dict[str, Any] or None
            The provenance data stored in the repository for the data entry.
            Returns `None` if no provenance data has been stored
        """
        raise NotImplementedError

    def put_provenance(self, provenance: dict[str, ty.Any], entry: DataEntry):
        """Stores provenance information for a given data item in the store

        Parameters
        ----------
        entry: DataEntry
            The entry to store the provenance data for
        provenance: dict[str, Any]
            The provenance data to store for the data entry
        """
        raise NotImplementedError

    def create_data_tree(
        self,
        id: str,
        leaves: list[tuple[str, ...]],
        space: type,
        hierarchy: list[str],
        id_composition: dict[str, str],
        **kwargs,
    ):
        """Creates a new dataset within the store, then creates an empty data tree
        specified by the provided leaf IDs. Used in dataset import/exports and in
        generated dummy data for test routines

        Parameters
        ----------
        id : str
            ID of the dataset
        leaves : list[tuple[str, ...]]
            list of IDs for each leaf node to be added to the dataset. The IDs for each
            leaf should be a tuple with an ID for each level in the tree's hierarchy, e.g.
            for a hierarchy of [subject, timepoint] ->
            [("SUBJ01", "TIMEPOINT01"), ("SUBJ01", "TIMEPOINT02"), ....]
        space : type (subclass of DataSpace)
            the "space" of the dataset
        hierarchy : list[str]
            the hierarchy of the dataset to be created
        id_composition : dict[str, str]
            Not all IDs will appear explicitly within the hierarchy of the data
            tree, and some will need to be inferred by extracting components of
            more specific labels.

            For example, given a set of subject IDs that combination of the ID of
            the group that they belong to and the member ID within that group
            (i.e. matched test & control would have same member ID)

                CONTROL01, CONTROL02, CONTROL03, ... and TEST01, TEST02, TEST03

            the group ID can be extracted by providing the a list of tuples
            containing ID to source the inferred IDs from coupled with a regular
            expression with named groups

                id_composition = {
                    'subject': r'(?P<group>[A-Z]+)(?P<member>[0-9]+)')
                }
        **kwargs
            Not used, but should be kept here to allow compatibility with future
            stores that may need to be passed other arguments
        """
        raise NotImplementedError

    ################################
    # RemoteStore-specific methods #
    ################################

    def download_files(self, entry: DataEntry, download_dir: Path) -> Path:
        """Download files associated with the given entry in the data store, using
        `download_dir` as temporary storage location (will be monitored by downloads
        in sibling processes to detect if download activity has stalled), return the
        path to a directory containing only the downloaded files

        Parameters
        ----------
        entry : DataEntry
            entry in the data store to download the files/directories from
        download_dir : Path
            temporary storage location for the downloaded files and/or compressed
            archives. Monitored by sibling processes to detect if download activity
            has stalled.

        Returns
        -------
        output_dir : Path
            a directory containing the downloaded files/directories and nothing else
        """
        raise NotImplementedError

    def upload_files(self, cache_path: Path, entry: DataEntry):
        """Upload all files contained within `input_dir` to the specified entry in the
        data store

        Parameters
        ----------
        input_dir : Path
            directory containing the files/directories to be uploaded
        entry : DataEntry
            the entry in the data store to upload the files to
        """
        raise NotImplementedError

    def download_value(
        self, entry: DataEntry
    ) -> ty.Union[float, int, str, list[float], list[int], list[str]]:
        """
        Extract and return the value of the field from the store

        Parameters
        ----------
        field : Field
            The field to retrieve the value for

        Returns
        -------
        value : int or float or str or list[int] or list[float] or list[str]
            The value of the Field
        """
        raise NotImplementedError

    def upload_value(self, value, entry: DataEntry):
        """
        Inserts or updates the field's value in the store

        Parameters
        ----------
        field : Field
            The field to insert into the store
        """
        raise NotImplementedError

    def create_fileset_entry(
        self, path: str, datatype: type, row: DataRow
    ) -> DataEntry:
        """
        Creates a new resource entry to store a field

        Parameters
        ----------
        path: str
            the path to the entry relative to the row
        datatype : type
            the datatype of the entry
        row : DataRow
            the row of the data entry

        Returns
        -------
        entry : DataEntry
            the created entry for the field
        """
        raise NotImplementedError

    def create_field_entry(self, path: str, datatype: type, row: DataRow) -> DataEntry:
        """
        Creates a new resource entry to store a field

        Parameters
        ----------
        path: str
            the path to the entry relative to the row
        datatype : type
            the datatype of the entry
        row : DataRow
            the row of the data entry

        Returns
        -------
        entry : DataEntry
            the created entry for the field
        """
        raise NotImplementedError

    def get_checksums(self, uri: str) -> dict[str, str]:
        """
        Downloads the checksum digests associated with the files in the file-set.
        These are saved with the downloaded files in the cache and used to
        check if the files have been updated on the server

        Parameters
        ----------
        uri: str
            uri of the data item to download the checksums for

        Returns
        -------
        checksums : dict[str, str]
            the checksums downloaded from the remote store
        """
        raise NotImplementedError

    def calculate_checksums(self, fileset: FileSet) -> dict[str, str]:
        """
        Calculates the checksum digests associated with the files in the file-set.
        These checksums should match the cryptography method used by the remote store
        (e.g. MD5, SHA256)

        Parameters
        ----------
        uri: str
            uri of the data item to download the checksums for

        Returns
        -------
        checksums : dict[str, str]
            the checksums calculated from the local file-set
        """
        raise NotImplementedError

    ##################
    # Helper methods #
    ##################
