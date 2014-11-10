canvas-cptool
=============

I am a CherryPy tool for authenticating and making calls to the [Canvas LMS API](https://canvas.instructure.com/doc/api/).

# Features

I can:
* Abstract away the entire OAuth2 Token Request Flow in a single line of code
* Prevent access to a page using a python decorator for a user without Canvas authentication (i.e. a valid token)
* Make memcachable API calls in one line
* Do all of the above with error handling taken care of; Exceptions are raised with (hopefully) helpful messages

# How it works

I use `cherrypy.session['canvas_user']` to store your Canvas API token, and the [currently-logged-in-user profile info](https://canvas.instructure.com/doc/api/users.html). If you are not authenticated yet, (or auth fails) I attempt to retrieve a token by taking the user through a complete OAuth2 Token Request Flow described in the Canvas API docs. Then I have an `.api` method which allows you to make calls to a Canvas API endpoint, and cache the  simplejson result for a given number of seconds (GET requests only). You can also make POST, PUT or DELETE requests with the api method, specified in the reqtype parameter.

Why do I do this? Because [simple is better than complex](http://legacy.python.org/dev/peps/pep-0020/). Authenticating and making API calls takes far too much boilerplate code, even while using the python requests library or [python-oauth2](https://github.com/simplegeo/python-oauth2). This simplifies authentication and API calls to a single line of code.

# Installation & Requirements

Be aware that I have many requirements including memcache (for caching) and mmh3 (for hash indexing). These can sometimes be a pain to install on some servers (as I've found out). You likely need to use your your package manager (such as `yum` or `apt-get`) to update/install more stuff which memcache and mmh3 require.

# Usage & Example

In a nutshell:

```python
cherrypy.tools.canvas = CanvasLMSTool.CanvasLMSTool(CANVAS_URL, CANVAS_CLIENT_ID, CANVAS_CLIENT_SECRET, MC)
canvas = cherrypy.tools.canvas  #just a shortcut

@cherrypy.expose
@cherrypy.tools.canvas()  #checks for a Canvas token, or forces user to perform the token request flow
def mycourses(self):
	# Get the Canvas user's list of courses and cache the result for 300 seconds
    courses = canvas.api('get', '/api/v1/courses', ttl=300)
    return course  #returning a simplejson object
```

The docstrings in CanvasLMSTool.py offer some additional info on the parameter types.

testCanvasTool.py is a basic example of a CherryPy app with the above in practice.

# FAQ

### I don't understand!?

I assume you know we are talking about the [LMS called Canvas made by Instructure](http://www.instructure.com/), and have read all the basics in their API docs, and have some experience working with CherryPy. I'm sorry for the lack of further documentation and examples. If you contact my auther (Isa), he may help you out if he has time.

### Is this secure?

In production, take care of securing your session variables, which is where the API tokens are stored.

### How do I "logout"?

Delete the cherrypy session variable `cherrypy.session['canvas_user']`. The user will then be unable to access any page which is protected by the tool's @decorator.

### Can this be used for any API that requires OAuth2?

I'm sure I can be abstracted further, but my author hasn't been inclined to do that yet.

### Who wrote this app?

I was initially written by Isa Hassen, who needed me for a very limited purpose. I know I am rather hastily written, he is sorry. Contributions are welcome.