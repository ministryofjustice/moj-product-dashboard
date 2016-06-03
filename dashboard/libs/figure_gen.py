from decimal import Decimal
from dashboard.libs.queries import get_dates
from dashboard.libs.date_tools import get_time_windows
from dashboard.apps.prototype.models import Project


class Figures(object):
    """
    To add different types of figure, create new methods
    in this class and then set the 'requested_figure'
    attribute in the request JSON to the name of the method.
    """

    @staticmethod
    def single_project(request_data):

        project = Project.objects.get(id=request_data['project_id'])

        if not project.tasks.exists():
            return []

        start_date, end_date = get_dates(request_data['start_date'], request_data['end_date'])

        project_start = project.tasks.order_by('start_date').first().start_date
        project_end = project.tasks.order_by('end_date').last().start_date

        if start_date < project_start:
            start_date = project_start
        if end_date > project_end:
            end_date = project_end

        time_windows = get_time_windows(start_date, end_date, request_data['time_increment'])

        response = []
        cumul_cost = Decimal()

        if start_date > project_start:
            cumul_cost += project.money_spent(project_start, start_date)

        for window in time_windows:
            time = project.time_spent(window[0], window[1])
            cost = project.money_spent(window[0], window[1])
            cumul_cost += cost
            staff_split = project.staff_split(window[0], window[1])
            label = window[2]

            if not request_data['filter_empty'] or time != 0:
                response.append({'time': time, 'cost': cost, 'cumul_cost': cumul_cost,
                                 'staff_split': staff_split, 'label': label})

        return response


def get_persons_on_project(project):
    tasks = project.tasks.all()

    persons = []
    for task in tasks:
        if task.person not in persons:
            persons.append(task.person)

    return persons


def get_data(request_data):

    data = getattr(Figures, request_data['request_type'])(request_data)

    return data

