canvas-cptool
=============

I am a CherryPy tool for authenticating and making calls to the [Canvas LMS API](https://canvas.instructure.com/doc/api/).

# Features

I can:
* Perform the entire OAuth2 Token Request Flow in a single line of code
* Require Canvas authentication with a python decorator
* Make memcachable API calls in one line
* Do all of the above with error handling taken care of; Exceptions are raised with (hopefully) helpful messages

# How it works

I use cherrypy.session['canvas_user'] to store your Canvas API token, and currently-logged-in-user profile info. If you are not authenticated yet, (or auth fails) I attempt to retrieve a token using the complete OAuth2 Token Request Flow described in the Canvas API docs. Then I have an .api method which allows you to make calls to a Canvas API endpoint, and cache the results of a GET request for a given number of seconds. That API method returns a simplejson object. You can also make POST, PUT or DELETE requests with the api method, specified in the reqtype parameter.

Why do I do this? Because [simple is better than complex](http://legacy.python.org/dev/peps/pep-0020/). Authenticating and making API calls takes far too much boilerplate code, even while using the python requests library. This simplifies authentication and API calls to a single line of code.

# Installation & Requirements

Be aware that I have many requirements including memcache (for caching) and mmh3 (for hash indexing). These can sometimes be a pain to install on some servers (as I've found out). Keep googling for answers is all the advice I can offer.

# Usage & Example

In a nutshell:

```python
cherrypy.tools.canvas = CanvasLMSTool.CanvasLMSTool(CANVAS_URL, CANVAS_CLIENT_ID, CANVAS_CLIENT_SECRET, MC)
canvas = cherrypy.tools.canvas # just a shortcut var name

@cherrypy.expose
@cherrypy.tools.canvas() # this line of code makes sure that the user has an API token, or makes him perform the token request flow
def mycourses(self):
	# Get the Canvas user's list of courses and cache the result for 300 seconds
    courses = canvas.api('get', '/api/v1/courses', ttl=300)
    return course # returning a plain simplejson object
```

Read the docstrings in CanvasLMSTool.py to learn the parameter types.

testCanvasTool.py is an example of how to protect a CherryPy page by requiring a Canvas API token, performing the token request flow (with the @decorator), and making a cached API call to view the user's current courses.

# FAQ

1. I don't understand!?

I assume you know we are talking about the LMS called Canvas made by Instructure, and have read all the basics of their API docs, and have some experience working with CherryPy. I'm sorry for the lack of further documentation and examples. If you contact my auther (Isa), he may help you out if he has time.

2. Is this secure?

In production, take care of securing your session variables, which is where the API tokens are stored.

3. Who wrote this app?

I was initially written by Isa Hassen, who needed me for a very limited purpose. I know I am rather hastily written, I'm sorry. Contributions are welcome.