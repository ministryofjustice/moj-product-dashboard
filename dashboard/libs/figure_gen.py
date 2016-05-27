from datetime import date

from dashboard.libs.queries import get_areas, get_persons, get_all_projects, get_tasks, get_dates
from dashboard.libs.date_tools import get_workdays_list
from dashboard.libs.rate_generator import get_reference_rate


class Figures(object):
    """
    To add different types of figure, create new methods
    in this class and then set the 'requested_figure'
    attribute in the request JSON to the name of the method.
    """

    @staticmethod
    def project_cost(data):

        if not data['projects']:
            return gen_empty_figure()

        project = data['projects'][0]
        persons = get_persons_on_project(project)
        rates = {}

        for person in persons:
            rates[person.float_id] = get_reference_rate(person.job_title, person.is_contractor)

        tasks = project.tasks.all()
        start_date = tasks.order_by('start_date')[0].start_date

        if project.end_date:
            end_date = project
        else:
            end_date = date.today()

        all_days = get_workdays_list(start_date, end_date)
        costs = []
        times = []

        for day in all_days:
            day_time = 0
            day_cost = 0
            for task in tasks:

                time = task.time_spent(day, day)
                cost = rates[task.person.float_id] * time

                day_time += time
                day_cost += cost

            costs.append(day_cost)
            times.append(day_time)

        data = {
            'start_date': start_date,
            'end_date': end_date,
            'data': {'days': all_days, 'costs': costs, 'times': times}
        }
        # import ipdb; ipdb.set_trace()
        return data

    @staticmethod
    def staff_split(data):
        contractor_percs = []
        cs_percs = []
        for project in data['projects']:
            persons = get_persons_on_project(project)

            num_contractors, num_civil_servants = count_staff_by_type(persons)

            if num_contractors == 0:
                contractor_percs.append(0)
            else:
                contractor_percs.append((num_contractors / (num_contractors + num_civil_servants)) * 100)
            if num_civil_servants == 0:
                cs_percs.append(0)
            else:
                cs_percs.append((num_civil_servants / (num_contractors + num_civil_servants)) * 100)

        project_names = [project.name for project in data['projects']]
        cs_trace = get_trace(project_names, cs_percs, 'Civil Servants')
        contr_trace = get_trace(project_names, contractor_percs, 'Contractors')

        layout = get_layout(barmode='stack')

        figure = {
            'data': [cs_trace, contr_trace],
            'layout': layout,
        }

        return figure


def gen_empty_figure():

    figure = {
        'data': [{}],
        'layout': {},
    }

    return figure


def get_layout(**kwargs):
    layout = {'showlegend': False}
    for key, value in kwargs.items():
        layout[key] = value
    return layout


def count_staff_by_type(persons):
    contractors = 0
    civil_servants = 0
    for person in persons:
        if person.is_contractor:
            contractors += 1
        else:
            civil_servants += 1
    return contractors, civil_servants


def get_persons_on_project(project):
    tasks = project.tasks.all()

    persons = []
    for task in tasks:
        if task.person not in persons:
            persons.append(task.person)

    return persons


def get_trace(x_axis, y_axis, name='trace', trace_type='bar'):
    trace = {
        'name': name,
        'x': x_axis,
        'y': y_axis,
        'type': trace_type
    }
    return trace


def get_figure(requested_figure, request_data):
    start_date, end_date = get_dates(request_data['start_date'], request_data['end_date'])
    data = {
        'persons': get_persons(request_data['persons']),
        'areas': get_areas(request_data['areas']),
        'projects': get_all_projects(request_data['projects']),  # Consider whether to limit by area here?
        'start_date': start_date,
        'end_date': end_date
    }
    try:
        figure = (getattr(Figures, requested_figure)(data))
    except AttributeError as err:
        figure = {}
        print('error: no such trace available')

    return figure
