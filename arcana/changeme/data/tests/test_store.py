import operator as op
from functools import reduce
import pytest
from pathlib import Path
import decimal
from fileformats.generic import File
from fileformats.field import Text as TextField
from fileformats.text import Plain as PlainText
from fileformats.generic import Directory
from fileformats.field import Integer, Decimal, Boolean, Array
from fileformats.testing import MyFormatGz, MyFormatGzX
from arcana.core.data.set import Dataset
from arcana.testing import TestDataSpace
from arcana.core.utils.serialize import asdict
from arcana.testing.data.blueprint import (
    TestDatasetBlueprint,
    FileSetEntryBlueprint as FileBP,
    FieldEntryBlueprint as FieldBP,
)
from conftest import dataset_defaults


TEST_DATASET_BLUEPRINTS = {
    "complete": TestDatasetBlueprint(  # dataset name
        space=TestDataSpace,
        hierarchy=["a", "b", "c", "d"],
        dim_lengths=[2, 2, 2, 2],
        entries=[
            FileBP(path="file1", datatype=PlainText, filenames=["file.txt"]),
            FileBP(path="file2", datatype=MyFormatGz, filenames=["file.my.gz"]),
            FileBP(path="file3", datatype=MyFormatGzX, filenames=["file.my.gz", "file.json"]),
            FileBP(path="dir1", datatype=Directory, filenames=["dir1"]),
            FieldBP(
                path="textfield",
                row_frequency="abcd",
                datatype=TextField,
                value="sample-text",
            ),  # Derivatives to insert
            FieldBP(
                path="booleanfield",
                row_frequency="c",
                datatype=Boolean,
                value="no",
                expected_value=False,
            ),  # Derivatives to insert
        ],
        derivatives=[
            FileBP(
                path="deriv1",
                row_frequency="abcd",
                datatype=PlainText,
                filenames=["file1.txt"],
            ),  # Derivatives to insert
            FileBP(
                path="deriv2",
                row_frequency="c",
                datatype=Directory,
                filenames=["dir"],
            ),
            FileBP(
                path="deriv3",
                row_frequency="bd",
                datatype=PlainText,
                filenames=["file1.txt"],
            ),
            FieldBP(
                path="integerfield",
                row_frequency="c",
                datatype=Integer,
                value=99,
            ),
            FieldBP(
                path="decimalfield",
                row_frequency="bd",
                datatype=Decimal,
                value="33.3333",
                expected_value=decimal.Decimal("33.3333"),
            ),
            FieldBP(
                path="arrayfield",
                row_frequency="bd",
                datatype=Array[Integer],
                value=[1, 2, 3, 4, 5],
            ),
        ],
    ),
}


@pytest.fixture(params=list(TEST_DATASET_BLUEPRINTS))
def dataset(data_store, work_dir, run_prefix, request):
    dataset_name = request.param
    blueprint = TEST_DATASET_BLUEPRINTS[dataset_name]
    dataset_id, space, hierarchy = dataset_defaults(
        data_store, dataset_name, run_prefix, work_dir
    )
    blueprint.space = space
    blueprint.hierarchy = hierarchy
    dataset = blueprint.make_dataset(data_store, dataset_id)
    return dataset


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_populate_tree(dataset: Dataset):
    blueprint = dataset.__annotations__["blueprint"]
    for freq in dataset.space:
        # For all non-zero bases in the row_frequency, multiply the dim lengths
        # together to get the combined number of rows expected for that
        # row_frequency
        num_rows = reduce(
            op.mul, (ln for ln, b in zip(blueprint.dim_lengths, freq) if b), 1
        )
        assert (
            len(dataset.rows(freq)) == num_rows
        ), f"{freq} doesn't match {len(dataset.rows(freq))} vs {num_rows}"


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_populate_row(dataset: Dataset):
    blueprint = dataset.__annotations__["blueprint"]
    for row in dataset.rows("abcd"):
        expected_paths = sorted(e.path for e in blueprint.entries)
        entry_paths = sorted(e.path for e in row.entries)
        assert entry_paths == expected_paths


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_get(dataset: Dataset):
    blueprint = dataset.__annotations__["blueprint"]
    for entry_bp in blueprint.entries:
        dataset.add_source(entry_bp.path, datatype=entry_bp.datatype)
    for row in dataset.rows(dataset.leaf_freq):
        for entry_bp in blueprint.entries:
            item = row[entry_bp.path]
            if item.is_fileset:
                item.trim_paths()
                assert sorted(p.name for p in item.fspaths) == sorted(
                    entry_bp.filenames
                )
            else:
                assert item.value == entry_bp.expected_value


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_post(dataset: Dataset):
    blueprint = dataset.__annotations__["blueprint"]

    def check_inserted():
        """Check that the inserted items are present in the dataset"""
        for deriv_bp in blueprint.derivatives:  # name, freq, datatype, _
            for row in dataset.rows(deriv_bp.row_frequency):
                cell = row.cell(deriv_bp.path, allow_empty=False)
                item = cell.item
                assert isinstance(item, deriv_bp.datatype)
                if deriv_bp.datatype.is_fileset:
                    assert item.hash_files() == all_checksums[deriv_bp.path]
                else:
                    assert item.raw_type(item.value) == item.raw_type(
                        deriv_bp.expected_value
                    )

    all_checksums = {}
    with dataset.tree:
        for deriv_bp in blueprint.derivatives:  # name, freq, datatype, files
            dataset.add_sink(
                name=deriv_bp.path,
                datatype=deriv_bp.datatype,
                row_frequency=deriv_bp.row_frequency,
            )
            test_file = deriv_bp.make_item()
            if deriv_bp.datatype.is_fileset:
                all_checksums[deriv_bp.path] = test_file.hash_files()
            # Test inserting the new item into the store
            with dataset.tree:
                for row in dataset.rows(deriv_bp.row_frequency):
                    row[deriv_bp.path] = test_file
        check_inserted()  # Check that cached objects have been updated
    check_inserted()  # Check that objects can be recreated from store


@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
def test_dataset_definition_roundtrip(dataset: Dataset):
    definition = asdict(dataset, omit=["store", "name"])
    definition["store-version"] = "1.0.0"

    data_store = dataset.store

    with data_store.connection:
        data_store.save_dataset_definition(
            dataset_id=dataset.id, definition=definition, name="test_dataset"
        )
        reloaded_definition = data_store.load_dataset_definition(
            dataset_id=dataset.id, name="test_dataset"
        )
    assert definition == reloaded_definition


# We use __file__ here as we just need any old file and can guarantee it exists
@pytest.mark.xfail(reason="Hasn't been implemented yet", raises=NotImplementedError)
@pytest.mark.parametrize("datatype,value", [(File, __file__), (TextField, "value")])
def test_provenance_roundtrip(datatype: type, value: str, simple_dataset: Dataset):
    provenance = {"a": 1, "b": [1, 2, 3], "c": {"x": True, "y": "foo", "z": "bar"}}
    data_store = simple_dataset.store

    with data_store.connection:
        entry = data_store.create_entry("provtest@", datatype, simple_dataset.root)
        data_store.put(datatype(value), entry)  # Create the entry first
        data_store.put_provenance(provenance, entry)  # Save the provenance
        reloaded_provenance = data_store.get_provenance(entry)  # reload the provenance
        assert provenance == reloaded_provenance
