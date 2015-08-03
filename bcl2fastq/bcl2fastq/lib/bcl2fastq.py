import subprocess
from lib.config import Config
import os.path

class Bcl2FastqConfig:
    """
    Container for configurations for bcl2fastq.
    Should handle setting up sensible defaults for
    values which have to be set.
    """
    def __init__(self,
                 bcl2fastq_version,
                 runfolder_input,
                 output,
                 barcode_mismatches=None,
                 tiles=None,
                 use_base_mask=None,
                 additional_args=None,
                 nbr_of_cores=None):

        self.runfolder_input = runfolder_input
        self.samplesheet = runfolder_input + "/Samplesheet.csv"
        self.base_calls_input = runfolder_input + "/Data/Intensities/BaseCalls"

        if bcl2fastq_version:
            self.bcl2fastq_version = bcl2fastq_version
        else:
            self.bcl2fastq_version = Bcl2FastqConfig.\
                get_bcl2fastq_version_from_run_parameters(runfolder_input)

        if output:
            self.output = output
        else:
            output_base = Config.load_config()["default_output_path"]
            runfolder_base_name = os.path.basename(runfolder_input)
            self.output = "{0}/{1}".format(output_base, runfolder_base_name)

        self.barcode_mismatches = barcode_mismatches
        self.tiles = tiles
        self.use_base_mask = use_base_mask
        self.additional_args = additional_args

        # Nbr of cores to use will default to the number of cpus on the system.
        if nbr_of_cores:
            self.nbr_of_cores = nbr_of_cores
        else:
            import multiprocessing
            self.nbr_of_cores = multiprocessing.cpu_count()

    @staticmethod
    def get_bcl2fastq_version_from_run_parameters(runfolder, config):
        """
        Guess which bcl2fastq version to use based on the machine type
        specified in the runfolder meta data, and the corresponding
        mappings in the config file.
        :param runfolder: to get bcl2fastq version to use for
        :return the version of bcl2fastq to use.
        """

        from illuminate.metadata import InteropMetadata
        meta_data = InteropMetadata(runfolder)
        model = meta_data.model

        current_config = config or Config.load_config()
        version = current_config["machine_type"][model]["bcl2fastq_version"]

        return version





class BCL2FastqRunnerFactory:
    """
    Generates new bcl2fastq runners according to the config passed.
    Will determine the correct runner to use based on the config,
    and the it's known binaries.
    """

    def __init__(self, config=None):
        if config:
            self.bcl2fastq_mappings = config["bcl2fastq"]["versions"]
        else:
            self.bcl2fastq_mappings = Config.load_config()["bcl2fastq"]["versions"]

    def _get_class_creator(self, version):
        """
        Based on the config provided in `bcl2fastq`, and the passed
        version, this will return a function that can be used to provide
        create a appropriate bcl2fastq runner.
        :param: version to look for mapping for
        :return: a function that can be used to create a bcl2fastq runner.
        """

        def _get_bcl2fastq2x_runner(self, config, binary):
            return BCL2Fastq2xRunner(config, binary)

        def _get_bcl2fastq1x_runner(self, config, binary):
            return BCL2Fastq1xRunner(config, binary)

        function_name = self.bcl2fastq_mappings[version]["class_creation_function"]
        function = locals()[function_name]
        return function

    def _get_binary(self, version):
        """
        Get the binary for the bcl2fastq version we are using.
        """
        return self.bcl2fastq_mappings[version]["binary"]

    def create_bcl2fastq_runner(self, config):
        """
        Uses higher order functions to create a correct runner based
        on the config passed to it.
        """
        version = config.bcl2fastq_version
        if version in self.bcl2fastq_mappings:
            clazz = self._get_class_creator(version)
            binary = self._get_binary(version)
            return clazz(self, config, binary)
        else:
            raise LookupError("Couldn't find a valid config mapping for bcl2fastq version {0}.".format(version))


class BCL2FastqRunner(object):
    """
    Base class for bcl2fastq runners. Provides common functionality for running commands, etc.
    """
    def __init__(self, config, binary):
        self.config = config
        self.binary = binary
        self.command = None

    def construct_command(self):
        """
        Implement this in subclass
        :return: a command to be run by `run`, or other external command runner.
        """
        raise NotImplementedError("Subclasses should implement this!")

    def run(self):
        """
        Will run the command provided by `_construct_command`
        :return: True is successfully run, else False.
        """
        #TODO Use logger!
        self.command = self.construct_command()
        print("Running bcl2fastq with command: " + self.command)

        try:
            output = subprocess.check_call(self.command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            #TODO Figure out better error processing (and logging here).
            print("Failure in running bcl2fastq!")
            print(exc)
            return False
        else:
            print("Successfully finished running bcl2fastq!")
            return True


class BCL2Fastq2xRunner(BCL2FastqRunner):
    """
    Runs bcl2fastq with versions 2.x
    """

    def __init__(self, config, binary):
        BCL2FastqRunner.__init__(self, config, binary)

    def construct_command(self):

        commandline_collection = [
            self.binary,
            "--input-dir", self.config.base_calls_input,
            "--output-dir", self.config.output]

        if self.config.barcode_mismatches:
            commandline_collection.append("--barcode-mismatches " + self.config.barcode_mismatches)

        if self.config.tiles:
            commandline_collection.append("--tiles " + self.config.tiles)

        if self.config.use_base_mask:
            commandline_collection.append("--use_base_mask " + self.config.use_base_mask)

        if self.config.additional_args:
            commandline_collection.append(self.config.additional_args)

        command = " ".join(commandline_collection)
        print("Generated command: " + command)
        return command

class BCL2Fastq1xRunner(BCL2FastqRunner):
    """Runs bcl2fastq with versions 1.x"""

    def __init__(self, config, binary):
        BCL2FastqRunner.__init__(self, config, binary)

    def construct_command(self):

        ##################################
        # First run configureBcl2fastq.pl
        ##################################

        # Assumes configureBclToFastq.pl on path
        commandline_collection = [
            "configureBclToFastq.pl",
            "--input-dir", self.config.base_calls_input,
            "--sample-sheet", self.config.samplesheet,
            "--output-dir", self.config.output,
            "--fastq-cluster-count 0", # No upper-limit on number of clusters per output file.
            "--force" # overwrite output if it exists.
        ]

        if self.config.barcode_mismatches:
            commandline_collection.append("--mismatches " + self.config.barcode_mismatches)

        if self.config.tiles:
            commandline_collection.append("--tiles " + self.config.tiles)

        if self.config.use_base_mask:
            commandline_collection.append("--use_bases_mask " + self.config.use_base_mask)

        if self.config.additional_args:
            commandline_collection.append(self.config.additional_args)

        ##################################
        # Then run make
        ##################################

        commandline_collection.append(" && make -j{0}".format(self.config.nbr_of_cores))

        command = " ".join(commandline_collection)
        print("Generated command: " + command)
        return command
