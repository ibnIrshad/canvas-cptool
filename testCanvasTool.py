import cherrypy
import CanvasLMSTool
import memcache

# This file stores my CANVAS_CLIENT_ID and CANVAS_CLIENT_SECRET. I'm not going to release that on Github
from secretglobals import *

# Do not include the trailing slash - this is where your Canvas installation is located
CANVAS_URL = 'https://my-canvas-installation.com'

MC = memcache.Client(['127.0.0.1:11211'], debug=0)
cherrypy.tools.canvas = CanvasLMSTool.CanvasLMSTool(CANVAS_URL, CANVAS_CLIENT_ID, CANVAS_CLIENT_SECRET, MC)
canvas = cherrypy.tools.canvas

class testCanvasTool(object):

    def __init__(self):
        pass

    @cherrypy.tools.canvas()
    @cherrypy.expose
    def index(self, **kwargs):

        returnvalue = 'You are logged in as: ' + kwargs['canvas_user']['name'] + '\n'
        returnvalue += '<h1>Your Courses</h1>\n'

        # Get the Canvas user's list of courses and cache the result for 300 seconds
        courses = canvas.api('get', '/api/v1/courses', ttl=300)

        for course in courses:
            returnvalue += course.get('name', str(course['id'])) + ' <br>\n'

        return returnvalue

cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 80,
                       })


cherrypy.quickstart(testCanvasTool(), '/', 'testCanvasTool.conf')

