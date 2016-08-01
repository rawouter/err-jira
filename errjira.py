# -*- coding: utf-8 -*-
from errbot import BotPlugin, CommandError
from errbot import botcmd, arg_botcmd
from itertools import chain
import re

CONFIG_TEMPLATE = {
    'API_URL': 'http://jira.example.com',
    'USERNAME': 'errbot',
    'PASSWORD': 'password',
    'PROJECT': 'FOO',
    'OAUTH_ACCESS_TOKEN': None,
    'OAUTH_ACCESS_TOKEN_SECRET': None,
    'OAUTH_CONSUMER_KEY': None,
    'OAUTH_KEY_CERT_FILE': None
}

try:
    from jira import JIRA, JIRAError
except ImportError:
    raise("Please install 'jira' python package")


class Jira(BotPlugin):
    """
    An errbot plugin for working with Atlassian JIRA
    """

    def _login_oauth(self):
        """
        Login to Jira with OAUTH
        """
        api_url = self.config['API_URL']
        if self.config['OAUTH_ACCESS_TOKEN'] is None:
            message = 'oauth configuration not set'
            self.log.info(message)
            return None

        key_cert_data = None
        cert_file = self.config['OAUTH_KEY_CERT_FILE']
        try:
            with open(cert_file, 'r') as key_cert_file:
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
            return None
        except TypeError:
            message = 'Unable to read key file {}'.format(cert_file)
            self.log.error(message)
            return None

    def _login_basic(self):
        """
        Login to Jira with basic auth
        """
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
            return None

    def _login(self):
        """
        Login to Jira
        """
        self.jira = self._login_oauth()
        if self.jira is None:
            self.jira = self._login_basic()
        return self.jira


    def activate(self):
        if self.config is None:
            message = 'Jira not configured.'
            self.log.info(message)
            self.warn_admins(message)
            return

        self.jira = self._login()
        if self.jira:
            super().activate()
        else:
            self.log.error('Failed to activate Jira plugin, maybe check the configuration')

    def configure(self, configuration):
        if configuration is not None and configuration != {}:
            config = dict(chain(CONFIG_TEMPLATE.items(), configuration.items()))
        else:
            config = CONFIG_TEMPLATE
        super(Jira, self).configure(config)

    def check_configuration(self, configuration):
        """
        Check the plugin config, raise errors
        """
        if not configuration.get('API_URL', '').lower().startswith('http'):
            raise Exception('Config validation failed for API_URL, this does not start with http')
        if not configuration.get('USERNAME', ''):
            raise Exception('Config validation failed for USERNAME, seems empty or not set')
        if not configuration.get('PASSWORD', ''):
            raise Exception('Config validation failed for PASSWORD, seems empty or not set')

    def get_configuration_template(self):
        """
        Returns a template of the configuration this plugin supports
        """
        return CONFIG_TEMPLATE

    def _send_msg(self, msg, message):
        self.send(
            msg.frm,
            message,
            message_type=msg.type,
            in_reply_to=msg,
            groupchat_nick_reply=True
        )

    def _find_one_user(self, msg, userstring):
        """
        Return one jira user corresponding to userstring.
        Stop the execution by raising a jira.CommandError if none or too many users found.
        """
        users = self.jira.search_assignable_users_for_projects(userstring, self.config['PROJECT'])
        if len(users) == 0:
            raise CommandError('No corresponding user found: {}'.format(userstring))
        elif len(users) > 1:
            raise CommandError('Too many user found: {}'.format(', '.join([u.name for u in users])))
        else:
            user = users[0]
        return user

    def _verify_issue_id(self, msg, issue):
        """
        Verify the issue ID is valid, if not raise a jira.CommandError and stop the execution.
        """
        issue = verify_and_generate_issueid(issue)
        if issue is None:
            raise CommandError('Issue id format incorrect')
        return issue

    @botcmd(split_args_with=' ')
    def jira_get(self, msg, args):
        """
        Describe a ticket. Usage: jira get <issue_id>
        """
        issue = self._verify_issue_id(msg, args.pop(0))
        try:
            issue = self.jira.issue(issue)
            self.send_card(
                title= issue.fields.summary,
                summary = 'Jira issue {}:'.format(issue),
                link=issue.permalink(),
                body=issue.fields.status.name,
                fields=(
                    ('Assignee',issue.fields.assignee.displayName),
                    ('Status',issue.fields.priority.name),
                ),
                color='red',
                in_reply_to=msg
            )
        except JIRAError:
            self._send_msg(msg, 'Error communicating with Jira, issue {} does not exist?'.format(issue))

    @arg_botcmd('summary', type=str)
    @arg_botcmd('-t', dest='type', type=str, default="Task")
    @arg_botcmd('-p', dest='priority', type=str)
    @arg_botcmd('-d', dest='description', type=str)
    def jira_create(self, msg, summary, type=None, priority=None, description=None):
        """
        Creates a new issue. Usage: jira create <summary> [@user] [-t <type>] [-p <priority>] [-d <description>]
        """
        if not summary:
            raise CommandError('You did not provide a summary.\nUsage: jira create <summary> [@user] [-t <type>] [-p <priority>] [-d <description>]')
        summary, username = get_username_from_summary(summary)
        self.jira.createmeta()
        #issue_dict = {
        #    'project': {'id': 123},
        #    'summary': 'New issue from jira-python',
        #    'description': 'Look into this one',
        #    'issuetype': {'name': 'Bug'},
        #}
        #new_issue = self.jira.create_issue(fields=issue_dict)

        return "Not implemented"

    @botcmd(split_args_with=None)
    def jira_assign(self, msg, args):
        """
        Assign a ticket. Usage: jira assign <issue_id> <username>
        """
        if len(args) != 2:
            raise CommandError('Wrong argument number.\nUsage: jira assign <issue_id> <username>')
        issueid = self._verify_issue_id(msg, args[0])
        user = self._find_one_user(msg, args[1])
        try:
            issue = self.jira.issue(issueid)
            self.jira.assign_issue(issue, user.name)
            self._send_msg(msg, 'Issue {} assigned to {}'.format(issue, user))
        except JIRAError:
            raise CommandError('Error communicating with Jira, issue {} does not exist?'.format(issue))

def verify_and_generate_issueid(issueid):
    """
    Take a Jira issue ID lowercase, or without a '-' and return a valid Jira issue ID.
    Return None if issueid can't be transformed
    """
    matches = []
    regexes = []
    regexes.append(r'([^\W\d_]+)\-(\d+)')  # e.g.: issue-1234
    regexes.append(r'([^\W\d_]+)(\d+)')    # e.g.: issue1234
    for regex in regexes:
        matches.extend(re.findall(regex, issueid, flags=re.I | re.U))
    if matches:
        for match in set(matches):
            return match[0].upper() + '-' + match[1]
    return None

def get_username_from_summary(summary):
    """
    If the summary string ends with `@someone`, return `someone`
    """
    lastword = summary.rsplit(None, 1)[-1]
    if lastword[0] == '@':
        return summary[:-len(lastword)-1], lastword[1:]
    return summary, None
