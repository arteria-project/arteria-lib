
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

        def row_to_sample_row(index_and_row):
            row = index_and_row[1]
            default_lane = 1 # MiSeq samplesheets do not contain any lane information - so we will default this to 1.
            default_index2 = ""
            return SampleRow(row.get("Lane", default_lane), row["Sample_ID"], row["Sample_Name"],
                             row["Sample_Plate"], row["Sample_Well"],
                             row["index"], row.get("index2", default_index2), row["Sample_Project"], row["Description"])

        lines_to_skip = find_data_line() + 1
        # Ensure that pointer is at beginning of file again.
        samplesheet_file_handle.seek(0)
        samplesheet_df = read_csv(samplesheet_file_handle, skiprows=lines_to_skip)
        samplesheet_df = samplesheet_df.fillna("")
        samples = map(row_to_sample_row, samplesheet_df.iterrows())
        return list(samples)
