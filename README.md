err-jira
=========

An errbot plugin for working with Atlassian JIRA.
Currently implemented:
- Search for a Jira issue ID
- Create issue
- Assign issue to valid user for the project
- Transition issue

OAuth for JIRA
----

Follow the guides on the JIRA developer pages:

- [Allowing oauth access](https://confluence.atlassian.com/jira/allowing-oauth-access-200213098.html "")
- [JIRA Rest APIs](https://developer.atlassian.com/jiradev/jira-apis/jira-rest-apis/jira-rest-api-tutorials/jira-rest-api-example-oauth-authentication "")
- [JIRA oauth python example](https://bitbucket.org/atlassian_tutorial/atlassian-oauth-examples/src/d625161454d1ca97b4515c6147b093fac9a68f7e/python/?at=default "")


Requirements
----

See requirements.txt:
`pip install -r requirements.txt`

Installation
----

```
  !repos install https://github.com/RaphYot/err-jira.git
  !plugin config Jira {'API_URL': 'http://jira.example.com', 'USERNAME': 'errbot', 'PASSWORD': 'password', 'PROJECT': 'FOO'}
  !plugin activate Jira
```
