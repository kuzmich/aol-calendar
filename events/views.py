from datetime import date

from django.http import Http404
from django.shortcuts import redirect, render

from .calendar import ARCHIVE_YEARS, YEARS, calendar_context


def home(request):
    return redirect('calendar_page', year=date.today().year)


def calendar_page(request, year):
    if year not in YEARS + ARCHIVE_YEARS:
        raise Http404
    context = calendar_context(year) | {'can_edit': request.user.is_staff}
    return render(request, 'events/page.html', context)
