import requests
import json
import yaml
import sys
from collections import defaultdict


class Gitlab_api():
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.file = 'projects_dirty.json'
        self.projects_json = 'project.json'
        super().__init__()

    def write_data(self, filename, data):
        try:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)
        except:
            print('Error')
            exit(1)

    def get_project(self):
        api_url = self.url + '/projects'
        header = {'PRIVATE-TOKEN': self.token}
        projects_json = []
        for page in range(1, 100):
            projects = requests.get(api_url, headers=header, params={'visibility': 'private', 'page': page})
            if len(projects.json()) == 20:
                for project in projects.json():
                    projects_json.append(project)
            else:
                for project in projects.json():
                    projects_json.append(project)
                break
        self.write_data(self.file, projects_json)
        return projects_json

    def project_convert(self):
        project_json = defaultdict(dict)

        with open(self.file) as file:
            data = json.load(file)
        for project in data:
            project_json[project['namespace']['name']][project['name']] = {}
            project_json['namespaces'][project['namespace']['name']] = {}

        self.write_data(self.projects_json, project_json)
        return project_json

    def project_convert_update(self):
        with open(self.file) as file:
            projects_new = json.load(file)

        with open(self.projects_json) as file:
            projects_sorted = json.load(file)

        for project in projects_new:
            if project['namespace']['name'] in projects_sorted['namespaces'].keys():
                if project['name'] not in projects_sorted[project['namespace']['name']].keys():
                    projects_sorted[project['namespace']['name']][project['name']] = {}
        self.write_data(self.projects_json, projects_sorted)
        return projects_sorted

    def load_projects(self):
        with open(self.projects_json) as file:
            projects = json.load(file)
        return projects

def load_conf():
    try:
        with open('config.yml', 'r') as file:
            config = yaml.load(file)
    except FileNotFoundError:
        print('File not found')
        sys.exit(1)
    except:
        print('Some error')
    return config

def main():
    config = load_conf()
    gitlab = Gitlab_api(config['gitlab_url'], config['gitlab_token'])
    project = gitlab.get_project()
    gitlab.write_data('projects_dirty.json', project)
    projects_json = gitlab.project_convert()
    gitlab.write_data('projects.json', projects_json)

if __name__ == '__main__':
    main()