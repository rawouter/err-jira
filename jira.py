# -*- coding: utf-8 -*-
from errbot import BotPlugin
from errbot import botcmd
from itertools import chain
import logging

log = logging.getLogger(name='errbot.plugins.Jira')

CONFIG_TEMPLATE = {'API_URL': "http://jira.example.com",
                   'USERNAME': 'errbot',
                   'PASSWORD': 'password',
                   'OAUTH_ACCESS_TOKEN': None,
                   'OAUTH_ACCESS_TOKEN_SECRET': None,
                   'OAUTH_CONSUMER_KEY': None,
                   'OAUTH_KEY_CERT_FILE': None,
                   'PROJECTS': ['FOO', 'BAR']}

try:
    from jira import JIRA, JIRAError
except ImportError:
    log.error("Please install 'jira' python package")


class Jira(BotPlugin):
    """An errbot plugin for working with Atlassian JIRA"""

    def activate(self):
        if self.config is None:
            # Do not activate the plugin until it is configured
            message = 'Jira not configured.'
            self.log.info(message)
            self.warn_admins(message)
            return

        self.jira_connect = self._login()
        if self.jira_connect:
            super().activate()

    def _login_oauth(self):
        """"""
        api_url = self.config['API_URL']

        if self.config['OAUTH_ACCESS_TOKEN'] is None:
            message = 'oauth configuration not set'
            self.log.error(message)
            return False

        key_cert_data = None
        try:
            with open(self.config['OAUTH_KEY_CERT_FILE'], 'r') as key_cert_file:
                key_cert_data = key_cert_file.read()
            oauth_dict = {
                'access_token': self.config['OAUTH_ACCESS_TOKEN'],
                'access_token_secret': self.config['OAUTH_ACCESS_TOKEN_SECRET'],
                'consumer_key': self.config['OAUTH_CONSUMER_KEY'],
                'key_cert': key_cert_data
            }
            authed_jira = JIRA(server=api_url, oauth=oauth_dict)
            self.log.info('logging into {} via oauth'.format(api_url))
            return authed_jira
        except JIRAError:
            message = 'Unable to login to {} via oauth'.format(api_url)
            self.log.error(message)
            return False
        except TypeError:
            message = 'Unable to read key file {}'.format(self.config['OAUTH_KEY_CERT_FILE'])
            self.log.error(message)
            return False


    def _login_basic(self):
        """"""
        api_url = self.config['API_URL']
        username = self.config['USERNAME']
        password = self.config['PASSWORD']
        try:
            authed_jira = JIRA(server=api_url, basic_auth=(username, password))
            self.log.info('logging into {} via basic auth'.format(api_url))
            return authed_jira
        except JIRAError:
            message = 'Unable to login to {} via basic auth'.format(api_url)
            self.log.error(message)
            return False

    def _login(self):
        """"""
        self.jira_connect = None
        self.jira_connect = self._login_oauth()
        if self.jira_connect:
            return self.jira_connect
        self.jira_connect = None
        self.jira_connect = self._login_basic()
        if self.jira_connect:
            return self.jira_connect
        return None

    def configure(self, configuration):
        if configuration is not None and configuration != {}:
            config = dict(chain(CONFIG_TEMPLATE.items(),
                                configuration.items()))
        else:
            config = CONFIG_TEMPLATE
        super(Jira, self).configure(config)

    def get_configuration_template(self):
        """Returns a template of the configuration this plugin supports"""
        return CONFIG_TEMPLATE

    def check_configuration(self, configuration):
        pass

    @botcmd(split_args_with=' ')
    def jira_get(self, msg, args):
        """Retrieves issue JSON from JIRA"""
        return "here's the content of issue XYZ"

    @botcmd(split_args_with=' ')
    def jira_create(self):
        """Creates a new JIRA issue"""
        """not implemented yet"""
        return "successfully created issue XYZ"

    @botcmd(split_args_with=' ')
    def jira_assign(self, msg, args):
        """Retrieves issue JSON from JIRA"""
        """not implemented yet"""
        return "assigned to user xyz"

    def callback_message(self, conn, mess):
        """A callback which responds to mentions of JIRA issues"""
        """not implemented yet"""
