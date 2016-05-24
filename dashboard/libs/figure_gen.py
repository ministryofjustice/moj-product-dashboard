from dashboard.libs.queries import get_areas, get_persons, get_all_projects, get_tasks, valid_date


class Figures(object):

    @staticmethod
    def _get_persons_on_project(project):
        tasks = project.tasks.all()

        persons = []
        for task in tasks:
            if task.person not in persons:
                persons.append(task.person)

        return persons

    @staticmethod
    def staff_split(data):

        # tasks = get_tasks(data['start_date'], data['end_date'])
        contractor_percs = []
        cs_percs = []
        for project in data['projects']:
            persons = Figures._get_persons_on_project(project)

            contractors = 0
            civil_servants = 0
            for person in persons:

                if person.is_contractor:
                    contractors += 1
                else:
                    civil_servants += 1

            contractor_percs.append((contractors / (contractors + civil_servants)) * 100)
            cs_percs.append((civil_servants / (contractors + civil_servants)) * 100)

        civ_servant_trace = {
            'x': [project.name for project in data['projects']],
            'y': [perc for perc in cs_percs],
            'name': 'Civil Servants',
            'type': 'bar',
        }

        contractors_trace = {
            'x': [project.name for project in data['projects']],
            'y': [perc for perc in contractor_percs],
            'name': 'Civil Servants',
            'type': 'bar',
        }

        layout = {

            'showlegend': False,
            'barmode': 'stack',

        },

        figure = {
            'data': [civ_servant_trace, contractors_trace],
            'layout': layout,
        }

        return figure


def get_figure(requested_figure, request_data):

    data = {
        'persons': get_persons(request_data['persons']),
        'areas': get_areas(request_data['areas']),
        'projects': get_all_projects(request_data['projects']),  # Consider whether to limit by area here?
        'start_date': valid_date(request_data['start_date']),
        'end_date': valid_date(request_data['end_date'])
    }

    try:
        figure = (getattr(Figures, requested_figure)(data))
    except AttributeError as err:
        figure = {}
        print('error: no such trace available')

    return figure
