from django.shortcuts import render

from .models import Points
from .utils import get_current_event_and_status_from_web, update_points_table_from_web


def index(request):
    current_event, points_are_final = get_current_event_and_status_from_web()
    latest_week_in_db = Points.objects.last().week

    if not points_are_final or not Points.objects.last().final_points:
        Points.objects.filter(week=current_event).delete()

    if (current_event - latest_week_in_db) > 1:
        for week in range(latest_week_in_db + 1, current_event):
            update_points_table_from_web(week, True)

    if not(current_event == latest_week_in_db and points_are_final):
        update_points_table_from_web(current_event, points_are_final)

    context = {
        'all_points': Points.objects.weekly_results(),
        'total_points_diff': Points.objects.total_points_diff(),
        'weekly_win_totals': Points.objects.get_win_totals_with_overall_rank(),
    }
    return render(request, 'app/index.html', context)
