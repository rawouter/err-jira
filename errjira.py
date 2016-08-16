# -*- coding: utf-8 -*-
from errbot import BotPlugin, CommandError
from errbot import botcmd, arg_botcmd, re_botcmd
from itertools import chain
import re

CONFIG_TEMPLATE = {
    'API_URL': 'http://atlassian.com',
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
            super(Jira, self).activate()
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

    def _find_one_user(self, msg, userstring):
        """
        Return one jira user corresponding to userstring.
        Stop the execution by raising a jira.CommandError if none or too many users found.
        """
        users = self.jira.search_assignable_users_for_projects(userstring, self.config['PROJECT'])
        if len(users) == 0:
            raise CommandError('No corresponding user found: {}'.format(userstring))
        elif len(users) > 1:
            raise CommandError('Too many users found: {}'.format(', '.join([u.name for u in users])))
        else:
            user = users[0]
        return user

    def _verify_issue_id(self, issue):
        """
        Verify the issue ID is valid, if not raise a jira.CommandError and stop the execution.
        """
        issue = verify_and_generate_issueid(issue)
        if issue is None:
            raise CommandError('Issue id format incorrect')
        return issue

    def _verify_transition_for_id(self, issueid, tname):
        """
        Ensure that a transition `tname` (case insensitive) is valid for `issueid` and return the transition
        ID that can be used to transition the issue.
        """
        issue = self._verify_issue_id(issueid)
        try:
            issue = self.jira.issue(issueid)
        except JIRAError:
            raise CommandError('Error connecting to Jira, issue {} might not exist'.format(issueid))
        transitions = self.jira.transitions(issue)
        transition_to_id = dict((x['name'].lower(), x['id']) for x in transitions)
        if tname.lower() not in transition_to_id.keys():
            raise CommandError('Transition {} does not exist, available transitions: {}'.format(
                tname,
                ''.join(['\n\t- '+x for x in transition_to_id.keys()]))
            )
        return transition_to_id[tname.lower()]

    @botcmd(split_args_with=' ')
    def jira_get(self, msg, args):
        """
        Describe a ticket. Usage: jira get <issue_id>
        """
        issue = self._verify_issue_id(args.pop(0))
        try:
            issue = self.jira.issue(issue)
            self.send_card(
                title= issue.fields.summary,
                summary = 'Jira issue {}: {}'.format(issue, msg.frm.person),
                link=issue.permalink(),
                body=issue.fields.status.name,
                fields=(
                    ('Assignee', issue.fields.assignee.displayName if issue.fields.assignee else 'None'),
                    ('Status',issue.fields.priority.name),
                ),
                color='red',
                in_reply_to=msg
            )
        except JIRAError:
            raise CommandError('Error communicating with Jira, issue {} does not exist?'.format(issue))

    @arg_botcmd('summary', type=str, nargs='+', help='Can end with @username to assign the task to `username`')
    @arg_botcmd('-t', dest='itype', type=str, default='Task', help='Task name')
    @arg_botcmd('-p', dest='priority', default='P3', type=str, help='Priority name')
    def jira_create(self, msg, summary, itype='Task', priority='P3'):
        """
        Creates a new issue.
        """
        summary = ' '.join(summary)
        if not summary:
            raise CommandError('You did not provide a summary.\nUsage: jira create [-t <type>] [-p <priority>] <summary> [@user]')
        summary, user = get_username_from_summary(summary)
        if user is not None:
            user = self._find_one_user(msg, user)
        try:
            issue_dict = {
                'project': self.config['PROJECT'],
                'summary': summary,
                'description': 'Reported by {} in errbot chat'.format(msg.frm.nick),
                'issuetype': {'name': itype},
                'priority': {'name': priority}
            }
            if user is not None:
                issue_dict['assignee'] = {'name': user.name}
            issue = self.jira.create_issue(fields = issue_dict)
            self.jira_get(msg, [issue.key])
        except JIRAError:
            return 'Something went wrong when calling Jira API, please ensure all fields are valid'

    @botcmd(split_args_with=None)
    def jira_transition(self, msg, args):
        """
        Transition a ticket. Usage: jira transition <issue_id> <transition_type>
        """
        if len(args) != 2:
            raise CommandError('Wrong argument number.\nUsage: jira transition <issue_id> <transition_type>')
        issueid = self._verify_issue_id(args[0])
        transition = self._verify_transition_for_id(issueid, args[1])
        self.jira.transition_issue(issueid, transition)
        self.jira_get(msg, [issueid])

    @botcmd(split_args_with=None)
    def jira_assign(self, msg, args):
        """
        Assign a ticket. Usage: jira assign <issue_id> <username>
        """
        if len(args) != 2:
            raise CommandError('Wrong argument number.\nUsage: jira assign <issue_id> <username>')
        issueid = self._verify_issue_id(args[0])
        user = self._find_one_user(msg, args[1])
        try:
            issue = self.jira.issue(issueid)
            self.jira.assign_issue(issue, user.name)
            return 'Issue {} assigned to {}'.format(issue, user)
        except JIRAError:
            raise CommandError('Error communicating with Jira, issue {} does not exist?'.format(issue))

    @re_botcmd(pattern=r"(^| )([^\W\d_]+)\-(\d+)( |$|\?|!\.)", prefixed=False, flags=re.IGNORECASE)
    def jira_listener(self, msg, match):
        """List for jira ID and display theyr summary"""
        try:
            self.jira_get(msg, ['-'.join(match.groups()[1:3]).upper()])
        except CommandError:
            pass


    @botcmd(split_args_with=None)
    def jira_jql(self, msg, args):
        """JQL search for a Jira tickets. Usage: jira search jql <JQL query>"""
        try:
            JQL = 'project='+self.config['PROJECT'] + ' and ' + ' '.join(args)
            for issue in self.jira.search_issues(JQL, maxResults=50):
                return 'link: This is [a link](http://www.errbot.net).'
                #yield '[{}]({}) - {} - {}'.format(issue, issue.permalink(), issue.fields.status.name, issue.fields.summary)
        except JIRAError as e:
            return  e.text

    @arg_botcmd('search', type=str, nargs='+', help='Search string')
    @arg_botcmd('--open', dest='open', action='store_true', help='Only open items')
    def jira_search(self, msg, search, open):
        """Search for a Jira tickets in description. Usage: jira search <text>"""
        args = ['(']
        args += ['summary', '~', '"'] + search + ['"']
        args += ['or', 'description', '~', '"'] + search + ['"']
        args += [')']
        if open:
            args += 'and status=Open'.split()
        args += 'order by created desc'.split()
        for issue in self.jira_jql(msg, args):
            return issue

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
