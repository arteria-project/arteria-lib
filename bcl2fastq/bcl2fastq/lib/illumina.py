
from pandas import read_csv

# TODO Implement picking up additional information from
# samplesheet. Right only picking up the data field is
# supported.

class SampleRow:
    def __init__(self, lane, sample_id, sample_name, sample_plate,
                 sample_well, index1, index2, sample_project, description):
        self.lane = int(lane)
        self.sample_id = str(sample_id)
        self.sample_name = str(sample_name)
        self.sample_plate = str(sample_plate)
        self.sample_well = str(sample_well)
        self.index1 = str(index1)
        self.index2 = str(index2)
        self.sample_project = str(sample_project)
        self.description = str(description)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if type(other) == type(self):
            return self.__dict__ == other.__dict__
        else:
            False

class Samplesheet:
    def __init__(self, samplesheet_file):
        self.samplesheet_file = samplesheet_file
        with open(samplesheet_file, mode="r") as s:
            self.samples = self._read_samples(s)

    @staticmethod
    def _read_samples(samplesheet_file_handle):

        def find_data_line():
            enumurated_lines = enumerate(samplesheet_file_handle)
            lines_with_data = filter(lambda x: "[Data]" in x[1], enumurated_lines)
            assert len(lines_with_data) == 1, "The wasn't strictly one line in samplesheet with line '[Data]'"
            return lines_with_data[0][0]

        # REVIEW If anyone has a better idea than this I'd be happy to head it.
        # The setup for this now is not pretty!
        # The Reason that this is done in this way is that not all fields
        # will exist depending on the type of run. In particular the "Lane" column
        # is not available in MiSeq samplesheets. /JD 20150813
        def row_to_sample_row(index_and_row):
            row = index_and_row[1]
            
            def single_index_row_to_sample_row(this_row, lane=None):
                  return SampleRow(lane or this_row["Lane"], this_row["Sample_ID"], this_row["Sample_Name"],
                                     this_row["Sample_Plate"], this_row["Sample_Well"],
                                     this_row["index"], "", this_row["Sample_Project"], this_row["Description"])

            def double_index_row_to_sample_row(this_row, lane=None):
                    return SampleRow(lane or this_row["Lane"], this_row["Sample_ID"], this_row["Sample_Name"],
                                     this_row["Sample_Plate"], this_row["Sample_Well"],
                                     this_row["index"], this_row["index2"], this_row["Sample_Project"], this_row["Description"])
            if "Lane" in row:
                if "index2" in row:
                    return double_index_row_to_sample_row(row)
                else:
                    return single_index_row_to_sample_row(row)
            else:
                if "index2" in row:
                    return double_index_row_to_sample_row(row, 1)
                else:
                    return single_index_row_to_sample_row(row, 1)

        lines_to_skip = find_data_line() + 1
        # Ensure that pointer is at beginning of file again.
        samplesheet_file_handle.seek(0)
        samplesheet_df = read_csv(samplesheet_file_handle, skiprows=lines_to_skip)
        samplesheet_df = samplesheet_df.fillna("")
        samples = map(row_to_sample_row, samplesheet_df.iterrows())
        return list(samples)
