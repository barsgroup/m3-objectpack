# Create your views here.rtn.core.views
from django.shortcuts import render_to_response
from m3.ui.app_ui import DesktopModel, DesktopLoader
from django import template as django_template
from django.views.decorators.csrf import csrf_exempt

def workspace(request):
    """docstring for workspace"""

    context = django_template.RequestContext(request, {
    })

    return render_to_response('demo_app/workspace.html', context)
