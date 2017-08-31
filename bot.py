import json
import sys

import requests
from flask import Flask
from flask import request, jsonify
from project import Gitlab_api
import yaml


class Bot(Gitlab_api):
    def __init__(self, host, port, token, ssl_cert, ssl_pkey):
        try:
            with open('config.yml', 'r') as file:
                config = yaml.load(file)
        except FileNotFoundError:
            print('File not found')
            sys.exit(1)
        except:
            print('Some error')

        super().__init__(url=config['gitlab_url'], token=config['gitlab_token'])
        self.host = host
        self.port = port
        self.token = token
        self.api = "https://api.telegram.org/bot%s/" % self.token
        self.ssl_cert = ssl_cert
        self.ssl_pkey = ssl_pkey
        self.chatid = set()

    def sendMessage(self, chat_id, msg):
        method = self.api + 'sendMessage'
        res = requests.post(method, json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'})
        answer = res.content
        answer_json = json.loads(answer)
        if not answer_json["ok"]:
            print(answer_json)
            sys.exit(1)
        else:
            return answer_json

    def send_to_all(self, msg):
        for chat in self.chatid:
            self.sendMessage(chat, msg)

    def send_to_subscriptions(self, project_name, msg):
        projects_list = self.load_projects()
        namespace, project = project_name.split(' / ')
        receivers = projects_list[namespace][project]
        print(receivers)
        for receiver in receivers:
            self.sendMessage(receiver, msg)

    def webhook(self):
        method = self.api + 'setWebhook'
        webhook_url = 'https://{0}:{1}/{2}'.format(self.host, self.port, self.token)
        data = {'url': webhook_url}
        if self.ssl_cert:
            webhook_params = {'certificate': open(self.ssl_cert, 'rb')}
            return requests.post(method, data=data, files=webhook_params)
        else:
            return requests.post(method, data=data)

    def InlineQuery(self, data):
        inline_query = {
            'id': data['inline_query']['id'],
            'from': data['inline_query']['from']['id'],
            'query': data['inline_query']['query']
        }
        return inline_query

    def answerInlineQuery(self, data):
        inline_query = self.InlineQuery(data)
        method = self.api + 'answerInlineQuery'
        answer = requests.post(method, json={'inline_query_id': inline_query['id'], 'cache_time': 30,
                                             'results': self.InlineQueryResultArticle(inline_query)})
        print(answer.json())
        return answer.status_code

    def InlineQueryResultArticle(self, inline_query):
        result = []
        i=1
        dictionary= self.InputTextMessageContent(inline_query)
        append_list = dictionary['append']
        remove_list = dictionary['remove']
        for project, title in append_list.items():
            result.append({'type': 'article', 'id': str(i), 'title': ('{0}  {1}'.format(title, project)),
                            'input_message_content': {
                                'message_text': ('/add_subscription {0} {1}'.format(title, project))}})
            i += 1
        for project, title in remove_list.items():
            result.append({'type': 'article', 'id': str(i), 'title': ('delete {0}  {1}'.format(title, project)),
                            'input_message_content': {
                                'message_text': ('/delete_subscription {0} {1}'.format(title, project))}})
            i += 1
        return result

    def InputTextMessageContent(self, inline_query):
        projects_dict = dict()
        projects_dict_rm = dict()
        projects_json = self.load_projects()
        for namespace, projects in projects_json.items():
            if len(inline_query['query']) > 2:
                if inline_query['query'] in namespace:
                    if inline_query['from'] in projects_json['namespaces'][namespace]:
                        projects_dict_rm[namespace] = 'namespace'
                    else:
                        projects_dict[namespace] = 'namespace'
                        for project in projects:
                            if inline_query['query'] in project:
                                if inline_query['from'] in projects[project]:
                                    projects_dict_rm[project] = 'project'
                                else:
                                    projects_dict[project] = 'project'
                else:
                    for project in projects:
                        if inline_query['query'] in project and 'namespaces' not in namespace:
                            if inline_query['from'] in projects[project]:
                                projects_dict_rm[project] = 'project'
                            else:
                                projects_dict[project] = 'project'
                        else:
                            continue
        return dict({'append': projects_dict, 'remove': projects_dict_rm})

    def getMe(self):
        method = self.api + 'getMe'
        return requests.get(method).json()


def main():
    pass