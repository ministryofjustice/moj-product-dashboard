from datetime import date

from dashboard.apps.prototype.models import Project
from dashboard.libs.queries import get_dates
from dashboard.libs.date_tools import get_workdays_list
from dashboard.apps.prototype.models import Project, Person, Task


class Figures(object):
    """
    To add different types of figure, create new methods
    in this class and then set the 'requested_figure'
    attribute in the request JSON to the name of the method.
    """

    @staticmethod
    def single_project(request_data):

        project = request_data['project']
        tasks = project.tasks.all()
        # Change to tasks.order_by('start_date').first() ?
        start_date = tasks.order_by('start_date')[0].start_date

        if project.end_date:
            end_date = project.end_date
        else:
            end_date = date.today()

        project_working_days = get_workdays_list(start_date, end_date)

        day_data = get_day_data(project_working_days, tasks)

        persons_data = get_persons_data(project)

        single_project_data = {
            'start_date': start_date,
            'end_date': end_date,
            'active_days': day_data,
            'persons': persons_data
        }

        return single_project_data


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


<<<<<<< HEAD
def get_data(request_data):

    data = getattr(Figures, request_data['request_type'])(request_data)

    return data
=======
def get_trace(x_axis, y_axis, name='trace', trace_type='bar'):
    trace = {
        'name': name,
        'x': x_axis,
        'y': y_axis,
        'type': trace_type
    }
    return trace


def get_figure(requested_figure, request_data):
    start_date, end_date = get_dates(request_data['start_date'],
                                     request_data['end_date'])
    # TODO we should split it into two views one for singular project
    # the other for a list
    if 'projectid' in request_data:
        project = Project.objects.get(id=request_data['projectid'])
    else:
        project = None

    if 'projectids' in request_data:
        projects = Project.objects.filter(id__in=request_data['projectids'])
    else:
        projects = None

    data = {
        #  'persons': get_persons(request_data['persons']),
        #  'areas': get_areas(request_data['areas']),
        'project': project,
        'projects': projects,
        'start_date': start_date,
        'end_date': end_date
    }
    try:
        figure = (getattr(Figures, requested_figure)(data))
    except AttributeError:
        figure = {}
        print('error: no such trace available')

    return figure
>>>>>>> develop
