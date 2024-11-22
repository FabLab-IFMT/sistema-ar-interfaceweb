from django.shortcuts import render
from .models import Action
from .scripts import FormattedAction
import datetime

# Create your views here.


def logs_list(request):
    dates = []

    for action in Action.objects.all():
        if action.date not in dates:
            dates.append(action.date)

    print(dates)

    return render(request, 'logs/logs_list.html', {'dates': dates })

def logs_datepage(request, day, month, year):
    actions = [FormattedAction(action) for action in Action.objects.all().order_by('time') if action.date == datetime.date(year, month, day) ]    
    date = datetime.date(year, month, day)

    return render(request, 'logs/logs_datepage.html', {'actions': actions, 'date': date})