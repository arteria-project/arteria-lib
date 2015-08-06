from tornado.testing import *

from tornado.escape import json_encode
import mock
from test_utils import TestUtils


from bcl2fastq.handlers.bcl2fastq_handlers import *
from bcl2fastq.app import create_app


class TestBcl2FastqHandlers(AsyncHTTPTestCase):

    API_BASE="/api/1.0"
    MOCK_BCL2FASTQ_DICT =  {1: "y*,iiiiiiii,iiiiiiii,y*",
                            2: "y*,iiiiii,n*,y*",
                            3: "y*,iiiiii,n*,y*",
                            4: "y*,iiiiiii,n*,y*",
                            5: "y*,iiiiiii,n*,y*",
                            6: "y*,iiiiiii,n*,y*",
                            7: "y*,iiiiiii,n*,y*",
                            8: "y*,iiiiiii,n*,y*",
                            }

    def get_app(self):
        return create_app(debug=False, auto_reload=False)

    def test_versions(self):
        with mock.patch.object(Config, 'load_config', return_value=TestUtils.DUMMY_CONFIG):
            response = self.fetch(self.API_BASE + "/versions")
            self.assertEqual(response.code, 200)
            self.assertEqual(sorted(json.loads(response.body)), sorted(["2.15.2", "1.8.4"]))

    def test_start_missing_runfolder_in_body(self):
        response = self.fetch(self.API_BASE + "/start/150415_D00457_0091_AC6281ANXX", method="POST", body = "")
        self.assertEqual(response.code, 500)

    def test_start(self):
        # Use mock to ensure that this will run without
        # creating the runfolder.
        with mock.patch.object(Config, 'load_config', return_value=TestUtils.DUMMY_CONFIG), \
             mock.patch.object(os.path, 'isdir', return_value=True), \
             mock.patch.object(Bcl2FastqConfig, 'get_bcl2fastq_version_from_run_parameters', return_value="2.15.2"), \
             mock.patch.object(Bcl2FastqConfig, 'get_bases_mask_per_lane_from_samplesheet', return_value=self.MOCK_BCL2FASTQ_DICT):

            body = {"runfolder_input": "/path/to/runfolder"}
            response = self.fetch(self.API_BASE + "/start/150415_D00457_0091_AC6281ANXX", method="POST", body=json_encode(body))

            self.assertEqual(response.code, 202)
            self.assertEqual(json.loads(response.body)["job_id"], 1)
            self.assertEqual(json.loads(response.body)["status_endpoint"], "/api/1.0/status/1")

    def test_status_with_id(self):
        response = self.fetch(self.API_BASE + "/status/1123456546", method="GET")
        self.assertEqual(response.code, 200)

    def test_status_without_id(self):
        response = self.fetch(self.API_BASE + "/status/", method="GET")
        self.assertEqual(response.code, 200)

    def test_all_stop_handler(self):
        response = self.fetch(self.API_BASE + "/stop/all", method="POST", body = "")
        self.assertEqual(response.code, 200)

    def test_stop_handler(self):
        response = self.fetch(self.API_BASE + "/stop/3", method="POST", body = "")
        self.assertEqual(response.code, 200)

    def test_exception_stop_handler(self):
        response = self.fetch(self.API_BASE + "/stop/lll", method="POST", body = "")
        self.assertEqual(response.code, 500)
