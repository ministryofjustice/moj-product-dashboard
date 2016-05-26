from dashboard.libs.queries import get_areas, get_persons, get_all_projects, get_tasks, get_dates


class Figures(object):
    """
    To add different types of figure, create new methods
    in this class and then set the 'requested_figure'
    attribute in the request JSON to the name of the method.
    """
    @staticmethod
    def staff_split(data):
        # tasks = get_tasks(data['start_date'], data['end_date'])
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

        cs_trace = get_trace(project_names, [perc for perc in cs_percs], 'Civil Servants')

        contr_trace = get_trace(project_names, [perc for perc in contractor_percs], 'Contractors')

        layout = get_layout(barmode='stack')

        figure = {
            'data': [cs_trace, contr_trace],
            'layout': layout,
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
