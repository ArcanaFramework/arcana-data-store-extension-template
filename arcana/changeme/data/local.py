from __future__ import annotations
import typing as ty
import logging
import attrs
from fileformats.core import FileSet, Field
from arcana.core.data.set.base import DataTree
from arcana.core.data.row import DataRow
from arcana.core.data.entry import DataEntry
from arcana.core.data.store import LocalStore


logger = logging.getLogger("arcana")


@attrs.define
class ExampleLocal(LocalStore):
    """A template store class for data stored on the local file-system in a specific
    structure. Please see the Attrs documentation (https://www.attrs.org/en/stable/)
    for instructions on how to design Python classes using the `attrs` package.

    For a data management system/data structure to be compatible with Arcana, it must
    meet a number of criteria. In Arcana, a store is assumed to

        * contain multiple projects/datasets addressable by unique IDs.
        * organise data within each project/dataset in trees
        * store arbitrary numbers of data "items" (e.g. "file-sets" and fields) within
          each tree node (including non-leaf nodes) addressable by unique "paths"
          relative to the node.
        * allow derivative data to be stored within in separate namespaces for different
          analyses on the same data
    """

    # Note this name will be constant, as there is only ever one store,
    # which covers whole FS
    name: str = "changeme"

    #################################
    # Abstract-method implementations
    #################################

    def populate_tree(self, tree: DataTree):
        """Scans the data present in the dataset and populates the nodes of the data
        tree with those found in the dataset using the ``DataTree.add_leaf`` method for
        every "leaf" node of the dataset tree.

        The order that the tree leaves are added is important and should be consistent
        between reads, because it is used to give default values to the ID's of data
        space axes not explicitly in the hierarchy of the tree.

        Parameters
        ----------
        dataset : Dataset
            The dataset to construct the tree dimensions for
        """
        raise NotImplementedError

    def populate_row(self, row: DataRow):
        """Scans a node in the data tree corresponding to the data row and populates a
        row with all data entries found in the corresponding node in the data
        store (e.g. files within a directory, scans within an XNAT session) using the
        ``DataRow.add_entry`` method. Within a node/row there are assumed to be two types
        of entries, "primary" entries (e.g. acquired scans) common to all analyses performed
        on the dataset and "derivative" entries corresponding to intermediate outputs
        of previously performed analyses. These types should be stored in separate
        namespaces so there is no chance of a derivative overriding a primary data item.

        The name of the dataset/analysis a derivative was generated by is appended to
        to a base path, delimited by "@", e.g. "brain_mask@my_analysis". The dataset
        name is left blank by default, in which case "@" is just appended to the
        derivative path, i.e. "brain_mask@".

        Parameters
        ----------
        row : DataRow
            The row to populate with entries
        """
        raise NotImplementedError

    def create_data_tree(
        self,
        id: str,
        leaves: list[tuple[str, ...]],
        hierarchy: list[str],
        space: type,
        **kwargs,
    ):
        """Creates a new empty dataset within in the store. Used in test routines and
        importing/exporting datasets between stores

        Parameters
        ----------
        id : str
            ID for the newly created dataset
        leaves : list[tuple[str, ...]]
                        list of IDs for each leaf node to be added to the dataset. The IDs for each
            leaf should be a tuple with an ID for each level in the tree's hierarchy, e.g.
            for a hierarchy of [subject, timepoint] ->
            [("SUBJ01", "TIMEPOINT01"), ("SUBJ01", "TIMEPOINT02"), ....]
        hierarchy: list[str]
            the hierarchy of the dataset to be created
        space : type(DataSpace)
            the data space of the dataset
        """
        raise NotImplementedError

    def get_fileset(self, entry: DataEntry, datatype: type) -> FileSet:
        """Retrieve the file-set associated with the given entry and return it cast
        to the specified datatype

        Parameters
        ----------
        entry : DataEntry
            the entry to retrieve the file-set for
        datatype : type (subclass DataType)
            the datatype to return the file-set as

        Returns
        -------
        FileSet
            the retrieved file-set
        """
        raise NotImplementedError

    def put_fileset(self, fileset: FileSet, entry: DataEntry) -> FileSet:
        """Put a file-set into the specified data entry

        Parameters
        ----------
        fileset : FileSet
            the file-set to store
        entry : DataEntry
            the entry to store the file-set in

        Returns
        -------
        FileSet
            the copy of the file-set that has been stored within the data entry
        """
        raise NotImplementedError

    def get_field(self, entry: DataEntry, datatype: type) -> Field:
        """Retrieve the field associated with the given entry and return it cast
        to the specified datatype

        Parameters
        ----------
        entry : DataEntry
            the entry to retrieve the field for
        datatype : type (subclass DataType)
            the datatype to return the field as

        Returns
        -------
        Field
            the retrieved field
        """
        raise NotImplementedError

    def put_field(self, field: Field, entry: DataEntry):
        """Put a field into the specified data entry

        Parameters
        ----------
        field : Field
            the field to store
        entry : DataEntry
            the entry to store the field in
        """
        raise NotImplementedError

    def fileset_uri(self, path: str, datatype: type, row: DataRow) -> str:
        """Returns the "uri" (e.g. file-system path relative to root dir) of a file-set
        entry at the given path relative to the given row

        Parameters
        ----------
        path : str
            path to the entry relative to the row
        datatype : type
            the datatype of the entry
        row : DataRow
            the row of the entry

        Returns
        -------
        uri : str
            the "uri" to the file-set entry relative to the data store
        """
        raise NotImplementedError

    def field_uri(self, path: str, datatype: type, row: DataRow) -> str:
        """Returns the "uri" (e.g. file-system path relative to root dir) of a field
        entry at the given path relative to the given row

        Parameters
        ----------
        path : str
            path to the entry relative to the row
        datatype : type
            the datatype of the entry
        row : DataRow
            the row of the entry

        Returns
        -------
        uri : str
            the "uri" to the field entry relative to the data store
        """
        raise NotImplementedError

    def get_fileset_provenance(
        self, entry: DataEntry
    ) -> ty.Union[dict[str, ty.Any], None]:
        """Retrieves provenance associated with a file-set data entry

        Parameters
        ----------
        entry : DataEntry
            the entry of the file-set to retrieve the provenance for

        Returns
        -------
        dict[str, ty.Any] or None
            the retrieved provenance or None if it doesn't exist
        """
        raise NotImplementedError

    def put_fileset_provenance(self, provenance: dict[str, ty.Any], entry: DataEntry):
        """Puts provenance associated with a file-set data entry into the store

        Parameters
        ----------
        provenance : dict[str, ty.Any]
            the provenance to store
        entry : DataEntry
            the entry to associate the provenance with
        """
        raise NotImplementedError

    def get_field_provenance(
        self, entry: DataEntry
    ) -> ty.Union[dict[str, ty.Any], None]:
        """Retrieves provenance associated with a field data entry

        Parameters
        ----------
        entry : DataEntry
            the entry of the field to retrieve the provenance for

        Returns
        -------
        dict[str, ty.Any] or None
            the retrieved provenance or None if it doesn't exist
        """
        raise NotImplementedError

    def put_field_provenance(self, provenance: dict[str, ty.Any], entry: DataEntry):
        """Puts provenance associated with a field data entry into the store

        Parameters
        ----------
        provenance : dict[str, ty.Any]
            the provenance to store
        entry : DataEntry
            the entry to associate the provenance with
        """
        raise NotImplementedError

    ##################
    # Helper functions
    ##################
