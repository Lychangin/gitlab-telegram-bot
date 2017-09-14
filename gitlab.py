import sys

import yaml
from flask import Flask
from flask import jsonify
from flask import request

from bot import Bot
from project import Gitlab_api


class Gitlab(Bot):
    def __init__(self, host, port, token, ssl_cert=None, ssl_pkey=None):
        super().__init__(host, port, token, ssl_cert, ssl_pkey,)

    def add_subscription(self, author, message):
        projects = self.load_projects()
        try:
            command, type, project = message.split()
            if type == 'namespace':
                projects['namespaces'][project] = set(projects['namespaces'][project])
                projects['namespaces'][project].add(author)
                projects['namespaces'][project] = list(projects['namespaces'][project])
            elif type == 'project':
                for namespace, projectss in projects.items():
                    if project in projectss:
                        projects[namespace][project] = set(projects[namespace][project])
                        projects[namespace][project].add(author)
                        projects[namespace][project] = list(projects[namespace][project])
            self.write_data(self.projects_json, projects)
            self.sendMessage(author, 'You add subscription')
        except ValueError:
            self.sendMessage(author, 'You must write project/namespace')


    def delete_subscription(self, author, message):
        projects = self.load_projects()
        try:
            command, type, project = message.split()
            if type == 'namespace':
                projects['namespaces'][project] = set(projects['namespaces'][project])
                try:
                    projects['namespaces'][project].remove(author)
                except KeyError:
                    print('Chat id not found')
                finally:
                    projects['namespaces'][project] = list(projects['namespaces'][project])
            elif type == 'project':
                for namespace, projectss in projects.items():
                    if project in projectss:
                        print(projects[namespace][project])
                        projects[namespace][project] = set(projects[namespace][project])
                        try:
                            projects[namespace][project].remove(author)
                        except KeyError:
                            print('Chat id not found')
                        finally:
                            projects[namespace][project] = list(projects[namespace][project])
            self.write_data(self.projects_json, projects)
            self.sendMessage(author, 'You delete subscription')
        except ValueError:
            self.sendMessage(author, 'You must write project/namespace')

    def list_subscription(self, data):
        list_projects = self.load_projects()
        subscription = []
        for namespace, projects in list_projects.items():
            for project, chatid in list_projects[namespace].items():
                if data["message"]['chat']['id'] in chatid:
                    if namespace in 'namespaces':
                        subscription.append('namespace {0}'.format(project))
                    else:
                        subscription.append('project {0}'.format(project))
        subscription_sorted = sorted(subscription)
        subscription_format = '\n'.join('{}'.format(item) for item in subscription_sorted)
        msg = 'Your Subscriptions:\n{}'.format(subscription_format)
        self.sendMessage(data["message"]['chat']['id'], msg)


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
    app = Flask(__name__)
    if config['cert'] == 'self-signed':
        bot = Gitlab(config['webhook_host'], config['webhook_port'], config['bot_token'], config['webhook_ssl_cert'],
                     config['webhook_ssl_private'])
    elif config['cert'] == 'official':
        bot = Gitlab(config['webhook_host'], config['webhook_port'], config['bot_token'])
    else:
        print('Error set webhook')
        sys.exit(1)
    bot.webhook()
    context = (config['webhook_ssl_cert'], config['webhook_ssl_private'])

    @app.route('/{0}'.format(bot.token), methods=['GET', 'POST'])
    def webhook_update():
        data = request.json
        if "message" in data:
            if "text" in data["message"]:
                if (data["message"]["text"]) == '/start' or (data["message"]["text"]) == '/start@gitlab_bot':
                    bot.sendMessage(data["message"]['chat']['id'],
                                    'This bot will help you:\
                                    \n- Notification status build Gitlab CI\
                                    \n- Add/Delete your subscriptions on projects or namespaces\
                                    \nTo search projects or namespaces type @gitlab_bot something and touch button')
                elif (data["message"]["text"]) == '/help' or (data["message"]["text"]) == '/help@gitlab_bot':
                    bot.sendMessage(data["message"]['chat']['id'],
                                    'This Bot send notification about build Gitlab CI:'
                                    '\n/list - List subscription'
                                    '\n/add_subscription {project name} - Add subscription'
                                    '\n/delete_subscription {project_name} - Delete subscription')
                elif (data["message"]["text"]) == '/list' or (data["message"]["text"]) == '/list@gitlab_bot':
                    bot.list_subscription(data)
                elif '/add_subscription' in (data["message"]["text"]):
                    bot.add_subscription(data["message"]['chat']['id'], data["message"]["text"])
                elif '/delete_subscription' in (data["message"]["text"]):
                    bot.delete_subscription(data["message"]['chat']['id'], data["message"]["text"])
                elif '/projects_pull' in (data["message"]["text"]):
                    bot.sendMessage(data["message"]['chat']['id'], 'Please, wait a few minutes')
                    gitlab.get_project()
                    bot.sendMessage(data["message"]['chat']['id'], 'That is ok')
                elif '/projects_convert' in (data["message"]["text"]): ## !!! Only the first time , second time is overwrite file
                    gitlab.project_convert()
                elif '/projects_update' in (data["message"]["text"]):
                    gitlab.project_convert_update()
                    bot.sendMessage(data["message"]['chat']['id'], 'That is ok')
        if "inline_query" in data:
            bot.answerInlineQuery(data)
        return jsonify({'status': 'ok'})

    @app.route('/build', methods=['GET', 'POST'])
    def pipeline():
        data = request.json
        msg = """\
-----------------------------------------------------
{0} run new build with tag {1}
Stage name {2}
Status Build <b>{3}</b>
Project <code>{4}</code>
Job <code>{5}/-/jobs/{6}</code>
User {7}
email {8}
-----------------------------------------------------""".format(data['user']['name'], data['ref'], \
                                                                data['build_name'], data['build_status'], \
                                                                data['repository']['homepage'], \
                                                                data['repository']['homepage'], \
                                                                data['build_id'], \
                                                                data['user']['name'], data['user']['email'])
        if data['build_status'] == 'success' or data['build_status'] == 'failed':
            bot.send_to_subscriptions(data['project_name'], msg)
        return jsonify({'status': 'ok'})

    app.run(host='0.0.0.0', port=bot.port, ssl_context=context)


if __name__ == '__main__':
    main()
