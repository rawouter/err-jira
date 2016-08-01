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

def test_get_username_from_summary():
    assert errjira.get_username_from_summary('foo bar') == ('foo bar', None)
    assert errjira.get_username_from_summary('foo bar me@myself') == ('foo bar me@myself', None)
    assert errjira.get_username_from_summary('foo @myself') == ('foo', 'myself')
    assert errjira.get_username_from_summary('foo bar cho @myself') == ('foo bar cho', 'myself')
    assert errjira.get_username_from_summary('@myself') == ('', 'myself')
