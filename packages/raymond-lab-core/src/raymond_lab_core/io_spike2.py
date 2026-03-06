from datetime import datetime
from sonpy import lib as sp

from .types import Spike2Data, Spike2FileHeader, Spike2ChannelInfo

def read_spike2_file(filepath: str) -> Spike2Data:
    """
    Reads a Spike2 file (.smr or .smrx) and extracts relevant data and metadata.

    Parameters:
    - filepath: Path to the Spike2 file to be read.

    Returns:
    - Spike2Data: A dataclass containing the extracted data and metadata from the Spike2 file.

    """
    try:
        spike2 = sp.SonFile(sName=str(filepath), bReadOnly=True)
        print(f"Reading Spike2 file: {filepath}")
    except Exception as e:
        print(f"Error reading Spike2 file: {e}")
        raise

    # # Extract header information
    # timedate = spike2.GetTimeDate()
    # hundredths, s, m, h, D, M, Y = timedate
    # microseconds = (hundredths * 10_000)
    # recording_date = datetime(Y, M, D, h, m, s, microseconds)

    # header = Spike2FileHeader(
    #     recording_date=recording_date,
    #     spike2_version=spike2.GetVersion(),
    #     file_comments=[spike2.GetComment(i) for i in range(spike2.MaxComments())],
    #     sample_rate=spike2.SampleRate(),
    #     channel_count=spike2.MaxChannels()
    # )

    # # Extract channel information and data
    # channels = {}
    # for i in range(spike2.MaxChannels()):
    #     if spike2.ChannelType(i) != sp.DataType.Off:
    #         channel_info = Spike2ChannelInfo(
    #             channel=i,
    #             title=spike2.ChannelTitle(i),
    #             type=str(spike2.ChannelType(i)),
    #             max_time=spike2.ChannelMaxTime(i),
    #             scale=spike2.ChannelScale(i),
    #             offset=spike2.ChannelOffset(i),
    #             units=spike2.ChannelUnits(i),
    #             divide=spike2.ChannelDivide(i),
    #             size=spike2.ChannelSize(i)
    #         )
    #         channels[i] = channel_info