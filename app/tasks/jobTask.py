# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from app import celery
import json,urllib
from app.common.httpHelp import httpRequset
from app import logger
from config import Config
from .mailTask import applyMail
from app.models.tickets import Tickets
@celery.task()
def projectJob(query):
    print json.dumps(query,indent=4)
    data = query['data']
    params = {
        'search': data['projectGroupName']
    }
    r = httpRequset(uri='/api/v4/groups',params=params,url=Config.CODEHUB_URL)
    if r.json():
        payload = {
            'name': data['projectName'],
            'namespace_id': r.json()[0]['id'],
            'visibility': 'internal'
        }
        uri = '/api/v4/projects'
        #create repo
        r = httpRequset(uri=uri, method="post", data=payload,url=Config.CODEHUB_URL)
        if r.status_code < 300:
            id = r.json()["id"]
            repoUrl = r.json()["http_url_to_repo"]
            #create file
            uri = '/api/v4/projects/{}/repository/files/README%2Emd'.format(id)
            payload = {
                'branch': 'master',
                'content': '',
                'commit_message': 'init commit'
            }
            httpRequset(uri=uri, method="post", data=payload,url=Config.CODEHUB_URL)
            #create_cmdb_project
            r = httpRequset(uri='/api/projectgroups')
            if r.status_code < 300:
                ids = [item['id'] for item in r.json()['data'] if item['name'] == data['projectGroupName']]
                if ids:
                    gid = ids[0]
                    payload = {
                        'name': data['projectName'],
                        'groupId': gid,
                        'describe': data['projectDescription'],
                        'projectType': data['projectType'],
                        'manager': data['owner'],
                        'repoUrl': repoUrl
                    }
                    r = httpRequset(uri='/api/projects', data=payload, method='post')
                    if r.status_code < 300:
                        projectId = r.json()['data']['id']
                        # create_domainName
                        domainName = data['domainName']
                        if domainName:
                            uri = '/api/dnsbatch/{}'.format(domainName)
                            r = httpRequset(uri=uri,url=Config.PACIFIC_URL,method='post')
                            logger().warn('{}\n{}'.format(query['id'], r.content))
                        q = Tickets.query.filter(Tickets.id==query['id']).first()
                        q.status = 'Complete'
                        q.commit()
                        toUser = Config.AUDITOR
                        toHander = Config.AUDITORHANDER
                        if query not in toUser:
                            toUser.append(query['email'])
                            toHander.append((query['requestMan'], query['email']))
                        content = {
                            "title": "Workflow工单申请",
                            "content": "<h4>您有一个新的工单已完成，工程名称：{}，ID为：{}，代码仓库地址为：{}</h4>".format(data['projectName'],projectId,repoUrl)
                        }

                        applyMail(toUser=toUser, toHander=toHander, mailArgs=content)
                    else:
                        logger().warn('{}\n{}'.format(query['id'], r.content))
                        return None
                else:
                    logger().warn('{}\n{}'.format(query['id'], 'cmdb_groupid not found'))
                    return None
            else:
                logger().warn('{}\n{}'.format(query['id'],r.content))
                return None
        else:
            logger().warn('{}\n{}'.format(query['id'], r.content))
            return None
    else:
        logger().warn('{}\n{}'.format(query['id'], 'codehub group not found'))
        return None
