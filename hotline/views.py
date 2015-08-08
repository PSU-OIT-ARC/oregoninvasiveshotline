import json
import random

from django.shortcuts import render

from hotline.reports.models import Report


def home(request):
    # get a random sampling of the last hundred public reports to display on the homepage
    reports = list(Report.objects.filter(is_public=True).order_by("-pk"))[:100]
    reports = random.sample(reports, min(len(reports), 10))
    reports_json = [report.to_json() for report in reports]
    return render(request, "home.html", {
        "reports_json": json.dumps(reports_json),
    })
