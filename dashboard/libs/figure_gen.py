from datetime import date

from dashboard.libs.queries import (get_areas, get_persons, get_all_projects,
                                    get_dates)
from dashboard.libs.date_tools import get_workdays_list
from dashboard.libs.rate_generator import get_reference_rate


class Figures(object):
    """
    To add different types of figure, create new methods
    in this class and then set the 'requested_figure'
    attribute in the request JSON to the name of the method.
    """

    @staticmethod
    def single_project(data):

        # Get a single project
        if not data['projects']:
            return gen_empty_figure()

        project = data['projects'][0]
        print('>>>>>>>>>>> ' + str(project))

        persons = get_persons_on_project(project)

        tasks = project.tasks.all()

        rates = demo_get_rates(persons)

        # Get the first day on the earliest task
        # Change to tasks.order_by('start_date').first() ?
        start_date = tasks.order_by('start_date')[0].start_date

        # Set the end date, if possible using data in the database
        if project.end_date:
            end_date = project.end_date
        else:
            end_date = date.today()

        # Get a list of the working days which occurred during the project's life-span
        project_working_days = get_workdays_list(start_date, end_date)

        day_data = get_day_data(project_working_days, tasks, rates)

        persons_data = get_persons_data(project)

        single_project_data = {
            'start_date': start_date,
            'end_date': end_date,
            'active_days': day_data,
            'persons': persons_data
        }

        return single_project_data

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


def get_persons_data(project):
    persons = get_persons_on_project(project)
    persons_data = []
    for person in persons:
        persons_data.append({'name': person.name, 'is_contractor': person.is_contractor,
                             'job_title': person.job_title})

    return persons_data


def demo_get_rates(persons):
    rates = {}

    for person in persons:
        rates[person.float_id] = get_reference_rate(person.job_title, person.is_contractor)

    return rates


def get_day_data(days, tasks, rates):

    active_days = []

    for day in days:
        day_time = 0
        day_cost = 0

        # Loop through all tasks and get the cost incurred on the given day, if any
        # ...this is probably needlessly slow. Probably an easier way to filter out tasks not
        # occurring on this day
        # import ipdb; ipdb.set_trace()
        for task in tasks:

            time = task.time_spent(day, day)

            if time:
                cost = task.person.rate_on(day) * time
                # cost = rates[task.person.float_id] * time
            else:
                cost = 0

            day_time += time
            day_cost += cost

        active_days.append({'date': day, 'cost': day_cost, 'person_days': day_time})

    return active_days


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


def get_data(requested_data, request_data):
    start_date, end_date = get_dates(request_data['start_date'], request_data['end_date'])
    data = {
        'persons': get_persons(request_data['persons']),
        'areas': get_areas(request_data['areas']),
        'projects': get_all_projects(request_data['projects']),  # Consider whether to limit by area here?
        'start_date': start_date,
        'end_date': end_date
    }

    # try:
    #     print(requested_data)
    #     figure = getattr(Figures, requested_data)(data)
    # except AttributeError as err:
    #     figure = {}
    #     print('error: no such trace available')

    figure = getattr(Figures, requested_data)(data)


    return figure
