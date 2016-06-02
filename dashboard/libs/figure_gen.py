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

        start_date, end_date = get_dates(request_data['start_date'], request_data['end_date'])

        project_start = project.tasks.order_by('start_date').first().start_date
        project_end = project.tasks.order_by('end_date').last().start_date

        if start_date < project_start:
            start_date = project_start
        if end_date > project_end:
            end_date = project_end

        time_windows = get_time_windows(start_date, end_date, request_data['time_increment'])

        response = []
        for window in time_windows:
            time = project.time_spent(window[0], window[1])
            cost = project.money_spent(window[0], window[1])
            label = window[2]

            if not request_data['filter_empty'] or time != 0:
                response.append({'time': time, 'cost': cost, 'label': label})

        return response


def get_persons_data(project):
    persons = get_persons_on_project(project)
    persons_data = []
    for person in persons:
        persons_data.append({'name': person.name, 'is_contractor': person.is_contractor,
                             'job_title': person.job_title})

    return persons_data


def get_day_data(days, tasks):

    active_days = []

    for day in days:
        day_time = 0
        day_cost = 0
        contractors = set()
        civil_servants = set()

        # Loop through all tasks and get the cost incurred on the given day, if any
        # ...this is probably needlessly slow. Probably an easier way to filter out tasks not
        # occurring on this day
        for task in tasks:

            time = task.time_spent(day, day)

            if time:
                cost = task.person.rate_on(day) * time

                if task.person.is_contractor:
                    contractors.add(task.person)
                else:
                    civil_servants.add(task.person)

            else:
                cost = 0

            day_time += time
            day_cost += cost

        contractor_perc, cs_perc = get_staff_percs(len(contractors), len(civil_servants))
        active_days.append({'date': day, 'cost': day_cost, 'person_days': day_time,
                            'contr_perc': contractor_perc, 'cs_perc': cs_perc})

    return active_days


def get_staff_percs(num_contractors, num_civil_servants):

    contractor_perc = 0
    cs_perc = 0
    if num_contractors != 0:
        contractor_perc = num_contractors / (num_contractors + num_civil_servants) * 100
    if num_civil_servants != 0:
        cs_perc = num_civil_servants / (num_contractors + num_civil_servants) * 100

    return contractor_perc, cs_perc


def get_persons_on_project(project):
    tasks = project.tasks.all()

    persons = []
    for task in tasks:
        if task.person not in persons:
            persons.append(task.person)

    return persons


def get_data(request_data):

    # import ipdb; ipdb.set_trace()

    data = getattr(Figures, request_data['request_type'])(request_data)

    return data

