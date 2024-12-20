from pathlib import Path

import pandas as pd
import pytest
import soundfile as sf

from OSmOSE import Dataset
from OSmOSE.cluster.audio_reshaper import reshape


@pytest.mark.unit
def test_reshape_errors(input_dir):
    with pytest.raises(ValueError) as e:
        reshape(
            input_files=input_dir,
            segment_size=20,
            datetime_begin="/not/a/datetime",
        )

    assert (
        str(e.value)
        == "The timestamp '/not/a/datetime' must match format %Y-%m-%dT%H:%M:%S%z."
    )

    with pytest.raises(ValueError) as e:
        reshape(
            input_files="/not/a/path",
            segment_size=15,
        )

    assert (
        str(e.value)
        == f"The input files must be a valid folder path, not '{Path('/not/a/path')!s}'."
    )

    with pytest.raises(FileNotFoundError) as e:
        reshape(
            input_files=input_dir,
            segment_size=20,
        )  # Supposed to fail because there is no timestamp.csv

    assert (
        str(e.value)
        == f"The timestamp.csv file must be present in the directory {Path(input_dir)} and correspond to the audio files in the same location, or be specified in the argument."
    )


@pytest.mark.unit
def test_reshape_smaller(input_dataset: Path, output_dir: Path):
    dataset = Dataset(
        input_dataset["main_dir"],
        gps_coordinates=(1, 1),
        depth=10,
        timezone="+03:00",
    )
    dataset.build(date_template="%Y%m%d_%H%M%S", original_folder="data/audio/original")

    reshape(
        input_files=dataset._get_original_after_build(),
        segment_size=2,
        output_dir_path=output_dir,
    )

    reshaped_files = [
        output_dir.joinpath(outfile)
        for outfile in pd.read_csv(
            str(output_dir.joinpath("timestamp_0.csv")),
            header=0,
        )["filename"].values
    ]

    assert len(reshaped_files) == 15
    assert sf.info(reshaped_files[0]).duration == 2.0
    assert sf.info(reshaped_files[0]).samplerate == 44100
    assert sum(sf.info(file).duration for file in reshaped_files) == 30.0


@pytest.mark.unit
def test_reshape_with_new_sr(input_dataset: Path, output_dir):
    dataset = Dataset(
        input_dataset["main_dir"],
        gps_coordinates=(1, 1),
        depth=10,
        timezone="+03:00",
    )
    dataset.build(date_template="%Y%m%d_%H%M%S", original_folder="data/audio/original")

    reshape(
        input_files=dataset._get_original_after_build(),
        segment_size=1,
        output_dir_path=output_dir,
        new_sr=800,
    )

    reshaped_files = [
        output_dir.joinpath(outfile)
        for outfile in pd.read_csv(
            str(output_dir.joinpath("timestamp_0.csv")),
            header=0,
        )["filename"].values
    ]

    assert len(reshaped_files) == 30
    assert sf.info(reshaped_files[0]).duration == 1.0
    assert sf.info(reshaped_files[0]).samplerate == 800
    assert sf.info(reshaped_files[-1]).duration == 1.0


@pytest.mark.unit
def test_reshape_truncate_last(input_dataset: Path, output_dir):
    dataset = Dataset(
        input_dataset["main_dir"],
        gps_coordinates=(1, 1),
        depth=10,
        timezone="+03:00",
    )
    dataset.build(date_template="%Y%m%d_%H%M%S", original_folder="data/audio/original")

    reshape(
        input_files=dataset._get_original_after_build(),
        segment_size=1,
        output_dir_path=output_dir,
    )

    reshaped_files = [
        output_dir.joinpath(outfile)
        for outfile in pd.read_csv(
            str(output_dir.joinpath("timestamp_0.csv")),
            header=0,
        )["filename"].values
    ]

    assert len(reshaped_files) == 30
    assert sf.info(reshaped_files[0]).duration == 1.0
    assert sf.info(reshaped_files[0]).samplerate == 44100
    assert sf.info(reshaped_files[-1]).duration == 1.0
