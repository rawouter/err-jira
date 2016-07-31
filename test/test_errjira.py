# -*- coding: utf-8 -*-
import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

import errjira

#from errbot.backends.test import FullStackTest
#
#
#class TestCommands(FullStackTest):
#
#    @classmethod
#    def setUpClass(cls, extra=None):
#        super(TestCommands, cls).setUpClass(__file__)
#
#    def test_jira(self):
#        self.assertCommand('!jira create project summary', 'created issue xxx')

def test_verify_and_generate_issueid():
    assert errjira.verify_and_generate_issueid('foo123') == 'FOO-123'
    assert errjira.verify_and_generate_issueid('foo-123') == 'FOO-123'
    assert errjira.verify_and_generate_issueid('Foo-123') == 'FOO-123'
    assert errjira.verify_and_generate_issueid('FOO-123') == 'FOO-123'
    assert errjira.verify_and_generate_issueid('foo') == None
