import pickle
from os.path import join

import numpy as np
import pandas as pd
from src.basics import FrameOperations


def test_load_1d_exp():
    fo = FrameOperations(data_type="Expression [RNA-seq]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Expression_files_present"]

    fo.sample_types = st
    frame, status = fo.load_1d("TP53")

    assert isinstance(status, str), "Status is not str."
    assert frame.empty is False, "Loaded frame is empty"
    assert set(frame.SampleType.unique()) == set(st), "Sample types not consistent with input."
    assert "TP53" in frame.columns, "Variable not present in dataframe."
    assert bool(frame.isna().sum().any()) is False, "Frame contains NaNs."


def test_load_1d_met():
    fo = FrameOperations(data_type="Methylation [450K/EPIC]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Methylation_files_present"]

    fo.sample_types = st
    frame, status = fo.load_1d("cg07779434")

    assert isinstance(status, str), "Status is not str."
    assert frame.empty is False, "Loaded frame is empty"
    assert set(frame.SampleType.unique()) == set(st), "Sample types not consistent with input."
    assert "cg07779434" in frame.columns, "Variable not present in dataframe."
    assert bool(frame.isna().sum().any()) is False, "Frame contains NaNs."


def test_load_1d_negative():
    fo = FrameOperations(data_type="Methylation [450K/EPIC]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Expression_files_present"]

    fo.sample_types = st
    frame, _ = fo.load_1d("XXX")
    assert frame.empty is True, "Loaded frame is not empty."


def test_load_many_exp():
    fo = FrameOperations(data_type="Expression [RNA-seq]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Expression_files_present"]

    fo.sample_types = st

    frame, status = fo.load_many(["TP53", "AIM2", "XXX"])
    assert isinstance(status, str), "Status is not str."
    assert frame.empty is False, "Loaded frame is empty."
    assert {"TP53", "AIM2"}.issubset(
        set(frame.columns)
    ), "Frame columns are not subset of variables."
    assert "XXX" not in frame.columns, "Unknown elements not removed from frame."
    assert bool(frame.isna().sum().any()) is False, "Frame contains NaNs."


def test_load_many_met():
    fo = FrameOperations(data_type="Methylation [450K/EPIC]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Expression_files_present"]

    fo.sample_types = st

    frame, status = fo.load_many(["cg07779434", "cg07779434"])
    assert isinstance(status, str), "Status is not str."
    assert frame.empty is False, "Loaded frame is empty."
    assert frame.shape[1] == 2, "Wrong shape of frame should be len(set(var)) + 1"
    assert bool(frame.isna().sum().any()) is False, "Frame contains NaNs."


def test_load_many_mvf_exp():
    fo = FrameOperations(data_type="Expression [RNA-seq]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Expression_files_present"]

    fo.sample_types = st

    frame_1, _ = fo.load_mvf(threshold=0.5)
    frame_2, _ = fo.load_mvf(threshold=0.7)

    assert set(frame_2.index).issubset(set(frame_1.index)), "Frame two should be a frame subset."
    assert set(frame_2.columns) == set(frame_1.columns), "Sample names do not match."
    assert bool(frame_1.isna().sum().any()) is False, "Frame 1 contains NaNs."
    assert bool(frame_2.isna().sum().any()) is False, "Frame 2 contains NaNs."


def test_load_many_mvf_met():
    fo = FrameOperations(data_type="Methylation [450K/EPIC]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Methylation_files_present"]

    fo.sample_types = st

    frame_1, _ = fo.load_mvf(threshold=0.5)
    frame_2, _ = fo.load_mvf(threshold=0.7)

    assert set(frame_2.index).issubset(set(frame_1.index)), "Frame two should be a frame subset."
    assert set(frame_2.columns) == set(frame_1.columns), "Sample names do not match."
    assert bool(frame_1.isna().sum().any()) is False, "Frame 1 contains NaNs."
    assert bool(frame_2.isna().sum().any()) is False, "Frame 2 contains NaNs."


def test_load_met_exp_frame():
    fo = FrameOperations(data_type="Methylation [450K/EPIC]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Methylation_expression_files_present"]

    fo.sample_types = st[0]
    frame, _ = fo.load_met_exp_frame("TP53", "cg07779434")

    assert (
        "TP53" in frame.columns and "cg07779434" in frame.columns
    ), "Frame does not contains vars."
    assert bool(frame.isna().sum().any()) is False, "Frame contains NaNs."


def test_load_met_exp_frame_neg():
    fo = FrameOperations(data_type="Methylation [450K/EPIC]", sample_types=None)
    with open(join(fo.basic_path, "global_metadata_file.pkl"), "rb") as file:
        file = pickle.load(file)
        st = file["Methylation_expression_files_present"]

    fo.sample_types = st[0]
    frame, _ = fo.load_met_exp_frame("XXX", "YYY")

    assert frame.empty is True, "Frame should be empty."


def test_binning():
    frame = pd.Series(np.linspace(0, 100, 100), name="XYZ")
    binned = FrameOperations.bin_variable(frame, n_bins=3)

    assert binned.nunique() == 3, "Wrong number of bins."
    assert binned.name == frame.name, "Wrongly specified name in binned series."


def test_scaling():
    frame = pd.Series(np.linspace(0, 100, 100), name="XYZ")
    scaled = FrameOperations.scale(frame, "Standard scaling")

    assert np.isclose(np.mean(scaled), 0), "Standard scaling mean error."
    assert np.isclose(np.var(scaled), 1), "Standard scaling var error."


def test_scaling_2():
    frame = pd.Series(np.linspace(0, 100, 100), name="XYZ")
    scaled = FrameOperations.scale(frame, None)

    assert frame.equals(scaled), "Scaling error."
