# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.testing.testing_helper module

Testing the test helper
"""
from datetime import datetime

import json
import os
import shutil


from keria.testing.testing_helper import Helpers

dirs=['cf','db','ks','mbx','not','opr','reg','reg/agent-fake','rks']
files=dict()
files['cf']='fake.json'

def test_helper():
    helpers = Helpers()
    pDir = "tmpUnitTestDir"

    if not os.path.exists(pDir):
        os.mkdir(pDir)
    assert True == os.path.exists(pDir)
    helpers.remove_test_dirs("fake",pDir)
    assert True == os.path.exists(pDir)
    
    for dir in dirs:
        tDir = pDir+f"/{dir}"
        if not os.path.exists(tDir):
            os.mkdir(tDir)
        if not os.path.exists(tDir+"/fake"):
            os.mkdir(tDir+"/fake")
        assert True == os.path.exists(tDir)
        helpers.remove_test_dirs("fake",pDir)
        assert False == os.path.exists(tDir+"/fake")
        assert True == os.path.exists(pDir)

    shutil.rmtree(pDir)