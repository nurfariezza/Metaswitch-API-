BASE_URL = 'https://billing.redtone.com'
TYPED_API = 'metaswitchapi1'
UNTYPED_API = 'metaswitchapi2'

def geturltyped(s):
    return '{0}/{1}/{2}'.format(BASE_URL, TYPED_API, s)

def geturluntyped(s):
    return '{0}/{1}/{2}'.format(BASE_URL, UNTYPED_API, s)