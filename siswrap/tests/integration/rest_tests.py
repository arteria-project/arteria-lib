import pytest
import requests
import time
import jsonpickle
from siswrap.configuration import *

# TODO: Improve the integration tests somewhat

class TestRestApi(object):
    BASE_URL = "http://testarteria1:10900/api/1.0"
    REPORT_URL = BASE_URL + "/report"
    QC_URL = BASE_URL + "/qc"

    CONF = "/opt/siswrap/etc/siswrap.config"

    STATE_NONE = "none"
    STATE_READY = "ready"
    STATE_STARTED = "started"
    STATE_DONE = "done"
    STATE_ERROR = "error"

    def __init__(self): 
        self.conf = ConfigurationService(self.CONF)

    def is_number(self, s): 
        try: 
            float(s)
            return True
        except ValueError: 
            return False

        try: 
            import unicodedata
            unicodedata.numeric(s)
            return True
        except (TypeError, ValueError): 
            return False

    def start_runfolder(self, handler, runfolder): 
        payload = {"runfolder": runfolder}

        if handler == "qc": 
            url = self.QC_URL + "/run/" + runfolder
        elif handler == "report": 
            url = self.REPORT_URL + "/run/" + runfolder

        resp = requests.post(url, json = payload)
        
        return resp

    def get_url(self, handler): 
        if handler == "qc": 
            return self.QC_URL
        elif handler == "report":
            return self.REPORT_URL

    def start_handler(self, handler): 
        runfolder = "foo"

        resp = self.start_runfolder(handler, runfolder)
        assert resp.status_code == 202

        payload = jsonpickle.decode(resp.text)

        assert payload.get("runfolder") == self.conf.get_setting("runfolder_root") + "/" + runfolder
        assert self.is_number(payload.get("pid")) is True
        pid = payload.get("pid")
        assert payload.get("state") == "started"
        assert payload.get("link") == self.get_url(handler) + "/status/" + str(pid)

        link = payload.get("link")

        resp = requests.get(link)
        assert resp.status_code == 202 or resp.status_code == 500

    def check_all_statuses(self, handler): 
        runfolders = ["foo", "bar"]
        firstresp = []
        pid = None

        # Request two new runs
        for runfolder in runfolders: 
            resp = self.start_runfolder(handler, runfolder)
            assert resp.status_code == 202

        # See so we get back statuses for both and the jobs have started
        resp = requests.get(self.get_url(handler) + "/status/")
        assert resp.status_code == 200
        payload = jsonpickle.decode(resp.text) 
        pid = str(payload[0].get("pid"))
    
        #assert len(payload) == len(runfolders)

        for run in payload:
            assert run.get("runfolder").split("/")[-1] in runfolders
            firstresp.append(run.get("state"))
            assert run.get("state") == "started" or run.get("state") == "error"

        if firstresp[0] == "started":
            # Sleep a little and check that the jobs have finished 
            time.sleep(60)
        
            resp = requests.get(self.get_url(handler) + "/status/")
            assert resp.status_code == 200
            payload = jsonpickle.decode(resp.text)
            pid = str(payload.get("pid"))

            for run in payload: 
                assert run.get("state") == "done" 

            # Request detailed status about one of the jobs 
            resp = requests.get(self.get_url(handler) + "/status/" + runfolders[0]) 
            assert resp.status_code == 404
            resp = requests.get(self.get_url(handler) + "/status/" + pid)
            assert resp.status_code == 202
            payload = jsonpickle.decode(resp.text) 

            # Detailed testing of the one status in separate function 

            # Afterwards the global status report should be decreased by one 
            resp = requests.get(self.get_url(handler) + "/status/")
            assert resp.status_code == 200 
            payload = jsonpickle.decode(resp.text) 

            assert payload.get("runfolder") == runfolders[1]
            assert payload.get("state") == "done"

            # And if we check the detailed status yet again then the process 
            # shouldn't still exist. 
            #assert len(payload) == len(runfolders) 
            resp = requests.get(self.get_url(handler) + "/status/" + runfolders[0])
            assert resp.status_code == 404
            resp = requests.get(self.get_url(handler) + "/status/" + pid)
            assert resp.status_code == 500
            payload = jsonpickle.decode(resp.text) 

            assert self.is_number(payload.get("pid")) is True
            assert payload.get("state") == "none"
        elif firstresp[0] == "error": 
            resp = requests.get(self.get_url(handler) + "/status/" + runfolders[0])
            assert resp.status_code == 404
            resp = requests.get(self.get_url(handler) + "/status/" + pid)
            assert resp.status_code == 500
#            payload = jsonpickle.decode(resp.text) 
#            assert payload.get("state") == "none"

    def test_basic_smoke_test(self):
        resp = requests.get(self.BASE_URL)
        assert resp.status_code == 200

    def test_can_start_a_report(self): 
        self.start_handler("report")

    def test_can_start_a_qc(self): 
        self.start_handler("qc")

    def check_a_status(self, handler): 
        runfolder = "foo"
       
        resp = self.start_runfolder(handler, runfolder)
        assert resp.status_code == 202
        
        payload = jsonpickle.decode(resp.text)
        pid = str(payload.get("pid"))

#        resp = requests.get(self.get_url(handler) + "/status/" + runfolder)
#        assert resp.status_code == 500

        resp = requests.get(self.get_url(handler) + "/status/" + pid)
        assert resp.status_code == 202
        payload = jsonpickle.decode(resp.text) 

        assert payload.get("state") == "started"
        assert payload.get("runfolder") == self.conf.get_setting("runfolder_root") + "/" + runfolder
        assert self.is_number(payload.get("pid")) is True

        # We want to make sure that the process has finished.
        time.sleep(60) 

        resp = requests.get(self.get_url(handler) + "/status/" + pid) 
        assert resp.status_code == 500 
        payload = jsonpickle.decode(resp.text) 
        assert payload.get("state") == "error"

        # Now when we have checked it again the process should be gone
        resp = requests.get(self.get_url(handler) + "/status/" + pid)
        assert resp.status_code == 500
        payload = jsonpickle.decode(resp.text) 
        assert payload.get("state") == "none"
       
    def test_can_check_a_report_status(self): 
        self.check_a_status("report")
    
    def test_can_check_a_qc_status(self): 
        self.check_a_status("qc")

    def test_can_check_all_report_statuses(self): 
        self.check_all_statuses("report")

    def test_can_check_all_qc_statuses(self): 
        self.check_all_statuses("qc")

if __name__ == '__main__':
    pytest.main()

