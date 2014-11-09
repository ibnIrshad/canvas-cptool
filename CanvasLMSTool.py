import requests
import cherrypy
import random
import sys
import simplejson as json
from mmh3 import hash128

AFTER_LOGIN_REDIR = '/'
LOGOUT_URL = '/logout'

class CanvasLMSTool(cherrypy.Tool):

    def __init__(self, canvas_url, canvas_client_id, canvas_client_secret, memcache_client=None):
        '''(CanvasLMSTool, str, str, str, memcache.Client) -> None'''

        cherrypy.Tool.__init__(self, 'before_handler', self.get_canvas_user, priority=1)
        self.token = None
        self.canvas_url = canvas_url
        self.ccid = canvas_client_id
        self.ccsec = canvas_client_secret
        self.MC = memcache_client

    def get_canvas_user(self):
        '''(CanvasLMSTool) -> json

        Perform a Canvas OAuth login routine if necessary and inject canvas_user into cherrypy.request.params which represents
        the current logged in user and their respective API key for Canvas (in canvas_user['token'])'''

        req = cherrypy.request

        if 'canvas_user' in cherrypy.session:
            cherrypy.log('canvas token present')
            cherrypy.request.params['canvas_user'] = json.loads(cherrypy.session['canvas_user'])
            return json.loads(cherrypy.session['canvas_user'])

        cherrypy.session.acquire_lock()

        if cherrypy.session.get('canvas_oath_state') == None:
            cherrypy.session['canvas_oath_redirect'] = redir = cherrypy.url(qs=cherrypy.request.query_string)
            cherrypy.session['canvas_oath_state'] = state = str(random.randint(1000, 9999))
            raise cherrypy.HTTPRedirect(self.canvas_url + '/login/oauth2/auth?client_id=' + self.ccid + '&response_type=code&redirect_uri=' + redir + '&state=' + state + '&purpose=Login_to_REP')
        
        if cherrypy.session.get('canvas_oath_state') != None:

            state = cherrypy.session['canvas_oath_state']
            cherrypy.session['canvas_oath_state'] = None

            if 'code' not in cherrypy.request.params or 'state' not in cherrypy.request.params:
                raise cherrypy.HTTPRedirect(AFTER_LOGIN_REDIR)
                #raise Exception('Please try to login to Canvas again. (Reason: missing code or state)')

            if cherrypy.request.params.get('error') == 'access_denied':
                raise Exception('Failed to login to Canvas, please check your username and password. (Reason: access_denied)')

            if state != cherrypy.request.params.get('state'):
                raise Exception('Failed to login to Canvas, please try again. (Reason: state mismatch)')

            data = {
                'client_id': self.ccid, 
                'redirect_uri': cherrypy.session.get('canvas_oath_redirect'),
                'client_secret': self.ccsec,
                'code': cherrypy.request.params['code']
            }
            
            r = requests.post(self.canvas_url + '/login/oauth2/token', data=data, verify=False)

            if r.status_code != 200:
                raise Exception('Failed to login to Canvas, please try again. Reason: ' + str(r.content))

            token = str(r.json()['access_token'])

            # Get user profile info 
            r = requests.get(self.canvas_url + '/api/v1/users/self/profile?access_token=' + token, verify=False)

            if r.status_code != 200:
                raise Exception('Failed to load user profile info, please try again.')


            userdata = r.json()
            userdata['token'] = token

            if sys.getsizeof(json.dumps(userdata)) > 4000:
                raise Exception('User profile information is too large to store in a cookie.')

            cherrypy.session['canvas_user'] = json.dumps(userdata)

            cherrypy.session.release_lock()

            raise cherrypy.HTTPRedirect(AFTER_LOGIN_REDIR)

        cherrypy.request.params['canvas_user'] = userdata
        return userdata


    def api(self, reqtype, endpoint, data=None, headers=None, ttl=180, error_msg=None):
        '''(CanvasLMSTool, str, dict or str, dict, int (number of seconds to live), str) -> json

        Return a json object which is the result of a Canvas API call to endpoint, and cache the request for ttl seconds.
        Raise an Exception with error_msg text in case of failure.'''

        endpoint = str(endpoint)
        assert reqtype in ['get', 'post', 'put', 'delete']
        assert isinstance(endpoint, str) and endpoint.startswith('/')
        assert data is None or isinstance(data, dict) or isinstance(data, str)
        assert isinstance(headers, dict) or headers is None
        assert error_msg is None or isinstance(error_msg, str)

        token = self.get_canvas_user()['token']

        error_msg = 'Failed to access Canvas. Location: ' + endpoint if error_msg is None else error_msg 

        if '?' in endpoint:
            endpoint += '&access_token=' + token
        else:
            endpoint += '?access_token=' + token

        if reqtype == 'get':
            key = str('CanvasAPICall_' + str(hash128(endpoint + str(data) + str(headers))))

            try:
                r = MC.get(key)
                if r is not None:
                    return json.loads(r)
            except:
                cherrypy.log('error accessing memcache')

            cherrypy.log('Request for ' + endpoint + ' not cached. Key: ' + key)

        req = getattr(requests, reqtype)

        try:
            content = ''
            r = req(self.canvas_url + endpoint, data=data, headers=headers, verify=False)
            if r.status_code in [401, 403]:
                delete_all_cookies()
                raise cherrypy.HTTPRedirect(LOGOUT_URL)
            if r.status_code != 200:
                content = r.content
        except:
            raise Exception(error_msg + ' ' + str(r.status_code) + ' ' + str(content))

        j = r.json()

        if reqtype == 'get':
            try:
                cherrypy.log('setting ' + key + ' :' + str(j))
                MC.set(key, json.dumps(j), ttl)
                print MC.get(key)
            except:
                pass
        
        return j



