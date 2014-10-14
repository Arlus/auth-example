from django.shortcuts import render_to_response, HttpResponseRedirect, Http404
from django.template.context import RequestContext
from django.contrib import messages
from django.conf import settings
from .forms import LoginForm
import httplib, urllib, cookielib, urllib2


def login(request):
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            username = data.get('username')
            password = data.get('password')
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain",
                       "User-Agent": "python"}
            cas_host = settings.CAS_HOST
            endpoint = settings.REST_ENDPOINT
            payload = urllib.urlencode({'username': username, 'password': password})
            # GET TGT
            connection = httplib.HTTPSConnection(cas_host)
            connection.request('POST', endpoint, payload, headers)
            response = connection.getresponse()
            data = response.read()
            location = response.getheader('location')
            if location is None:
                form = LoginForm(initial={'username': username})
                messages.add_message(request, messages.ERROR, 'Invalid credentials.')
                return render_to_response("login.html", locals(), context_instance=RequestContext(request))
            TGT = location[location.rfind('/') + 1:]
            connection.close()
            import sys

            sys.stderr.write("******************************")
            sys.stderr.write("TGT: {0}".format(TGT))
            sys.stderr.write("Location header: {0}".format(location))
            sys.stderr.write("******************************")

            #Grab a service ticket for a CAS protected service
            service = 'http://www.smarteragent.com{0}'.format(settings.SECURE_SERVICE)
            payload = urllib.urlencode({'service': service})
            connection = httplib.HTTPSConnection(cas_host)
            connection.request("POST", "{0}{1}".format(endpoint, TGT), payload, headers)
            response = connection.getresponse()
            service_ticket = response.read()
            connection.close()
            url = "{0}?ticket={1}".format(service, service_ticket)
            cookie_jar = cookielib.CookieJar()
            # no proxies please
            no_proxy_support = urllib2.ProxyHandler({})
            # we need to handle session cookies AND redirects
            cookie_handler = urllib2.HTTPCookieProcessor(cookie_jar)
            opener = urllib2.build_opener(no_proxy_support, cookie_handler, urllib2.HTTPHandler(debuglevel=1))
            urllib2.install_opener(opener)
            protected_data = urllib2.urlopen(url).read()

            #Service ticket validation
            request.session['service'] = service
            request.session['ticket'] = service_ticket

            return render_to_response("dashboard.html", locals(), context_instance=RequestContext(request))
    form = LoginForm()
    return render_to_response("login.html", locals(), context_instance=RequestContext(request))


def validate(request):
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain",
               "User-Agent": "python"}
    payload = urllib.urlencode({'service': request.session['service'], 'ticket': request.session['ticket']})
    connection = httplib.HTTPSConnection(settings.CAS_HOST)
    connection.request('POST', settings.REST_VALIDATE, payload, headers)
    response = connection.getresponse()
    answer = response.read()
    import sys

    sys.stderr.write("******************************")
    sys.stderr.write("XML Answer: {0}".format(response.status))
    sys.stderr.write("XML Answer: {0}".format(response.reason))
    sys.stderr.write("******************************")

    messages.add_message(request, messages.INFO, 'Service ticket validated')
    return render_to_response("dashboard.html", locals(), context_instance=RequestContext(request))