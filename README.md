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

Feature examples:
----

```
 >>> jira create This is an example @raph -p P3

  Jira issue BDBDEV-585:

  This is an example ()

 Open
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Assignee        ┃ Status ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Raphael Wxxxxxx │ P3     │
└─────────────────┴────────┘

 >>> jira assign bdbdev-586 sam

  Issue BDBDEV-586 assigned to Sam Gxxxxx

 >>> what about bdbdev-586? # This bot listen for Jira ID.

  Jira issue BDBDEV-586:

  This is an example ()

 Open
┏━━━━━━━━━━━━┳━━━━━━━━┓
┃ Assignee   ┃ Status ┃
┡━━━━━━━━━━━━╇━━━━━━━━┩
│ Sam Gxxxxx │ P3     │
└────────────┴────────┘

 >>> jira transition bdbdev-586 foo

  Transition foo does not exist, available transitions: monitor
    - open
    - doing
    - deploy
    - test
    - close


 >>> jira transition bdbdev-586 close

 Jira issue BDBDEV-586:

  This is an example ()

 Closed
┏━━━━━━━━━━━━┳━━━━━━━━┓
┃ Assignee   ┃ Status ┃
┡━━━━━━━━━━━━╇━━━━━━━━┩
│ Sam Gxxxxx │ P3     │
└────────────┴────────┘

```
