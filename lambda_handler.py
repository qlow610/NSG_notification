#coding:utf-8

from __future__ import print_function

import base64
import json
import logging
import os
import zlib
import pprint
import boto3
import datetime

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ec2 = boto3.client('ec2')

slackurl = os.environ['slackurl']


def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    data = zlib.decompress(base64.b64decode(event['awslogs']['data']), 16+zlib.MAX_WBITS)
    data_json = json.loads(data)
    logger.info("Event: " + str(data_json))
    ID = json.loads(json.dumps(data_json["logEvents"]))
    for j in ID:
        cidrIp = []
        log2 = json.loads(ｊ['message'])
        #pprint.pprint(log2)
        Action = log2['eventName']
        if 'RevokeSecurityGroupIngress' in Action:
            Event = "NSGからIPが削除されました。"
        elif 'AuthorizeSecurityGroupIngress' in Action:
            Event = "NSGにIPが追加されました。"
        else:
            Event = Action
        user =  log2['userIdentity']['userName']
        eventTime = log2['eventTime']
        del_table = str.maketrans({'T': ' ', 'Z':None,'-':'/'})
        eventTime = eventTime.translate(del_table)
        eventTime = datetime.datetime.strptime(eventTime,'%Y/%m/%d %H:%M:%S')
        eventTime = str(eventTime + datetime.timedelta(hours=9))
        items = log2['requestParameters']['ipPermissions']['items']
        temp_message = []
        for i in items:
            Port = str(i['fromPort'])
            pprint.pprint(i)
            if i['ipRanges'].get('items') is None:
                cidrIp = i['ipv6Ranges']['items'][0]['cidrIpv6']
                if 'description' not in i['ipv6Ranges']['items'][0].keys():
                    description = '-'
                else:
                    description = i['ipv6Ranges']['items'][0]['description']
            else:
                cidrIp = i['ipRanges']['items'][0]['cidrIp']
                if 'description' not in i['ipRanges']['items'][0].keys():
                    description = '-'
                else:
                    description = i['ipRanges']['items'][0]['description']
            temp_fields = [{
                "title":cidrIp,
                "value": "Description:" + description + '\n Port :' + Port,
                "short": "true"
                }]
            temp_message.extend(temp_fields)
        Tergetid = log2['requestParameters']['groupId']
        Describe_SG = ec2.describe_security_groups(GroupIds=[Tergetid])
        Tags = Describe_SG['SecurityGroups'][0]['Tags']
        name_tag = '-'
        for k in Tags:
            if k['Key'] == 'Name':
                name_tag = k['Value']
        temp_message = [
                    {
                        'title': 'Infomation',
                        'value': 'Username :' + user + '\n EventTime : ' + eventTime,
                        'short': True
                    },
                    {
                        'title': 'SG',
                        'value': 'Name :' + name_tag + '\n' + 'SGID :' + Tergetid,
                        'short': True
                    }
                        ]
        temp_fields = temp_message +temp_fields
        message_json = {
            'username': 'AWS Cloud Trail Infomation',
            'icon_emoji': ':awsicon:',
            'text': 'NSGの変更を検知しました',
            'attachments': [
                {
                'fallback': 'AWS CloudTrail Info',
                'color': 'warning',
                'title': Event,
                'fields': temp_fields
                }
            ]
        }
        req = Request(slackurl, json.dumps(message_json).encode('utf-8'))
        try:
            response = urlopen(req)
            response.read()
            logger.info("Message posted.")
        except HTTPError as e:
            logger.error("Request failed: %d %s", e.code, e.reason)
        except URLError as e:
            logger.error("Server connection failed: %s", e.reason)