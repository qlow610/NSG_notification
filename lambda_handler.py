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
    message_json = []
    logger.info("Event: " + str(event))
    data = zlib.decompress(base64.b64decode(event['awslogs']['data']), 16+zlib.MAX_WBITS)
    data_json = json.loads(data)
    logger.info("Event: " + str(data_json))
    ID = json.loads(json.dumps(data_json["logEvents"]))
    for J in ID:
        log2 = json.loads(J['message'])
        eventTime = log2['eventTime']
        del_table = str.maketrans({'T': ' ', 'Z':None,'-':'/'})
        eventTime = eventTime.translate(del_table)
        eventTime = datetime.datetime.strptime(eventTime,'%Y/%m/%d %H:%M:%S')
        eventTime = str(eventTime + datetime.timedelta(hours=9))
        Action = log2['eventName']
        Eventsource = log2['eventSource']
        user =  log2['userIdentity']['userName']
        if 'iam.amazonaws.com' in Eventsource:
            IamNotifi(log2,user,eventTime,Action,message_json)
        elif 'ec2.amazonaws.com' in Eventsource:
            NSGnotifi(log2,eventTime,Action,user,message_json)
        else :
            logger.info("Unknown: " + str(log2))
            message_json = {
                'username': 'AWS Cloud Trail Infomation',
                'icon_emoji': ':awsicon:',
                'text': '定義されていないMSGを検知しました'}
            slacknotification(message_json)

def slacknotification(message_json):
        req = Request(slackurl, json.dumps(message_json).encode('utf-8'))
        try:
            response = urlopen(req)
            response.read()
            logger.info("Message posted.")
        except HTTPError as e:
            logger.error("Request failed: %d %s", e.code, e.reason)
        except URLError as e:
            logger.error("Server connection failed: %s", e.reason)

def IamNotifi(log2,user,eventTime,Action,message_json):
    if 'userName' in log2['requestParameters'].keys():
        Name = log2['requestParameters']['userName']
        
    elif 'roleName' in log2['requestParameters'].keys():
        Name = log2['requestParameters']['roleName']
    elif 'groupName' in log2['requestParameters'].keys():
        Name = log2['requestParameters']['groupName']
    elif 'instanceProfileName' in log2['requestParameters'].keys():
        Name = log2['requestParameters']['instanceProfileName']
    else:
        Name = "-"
    temp_message = [
    {
        'title': 'Information',
            'value': 'Username :' + user + '\n' + 'EventTime : ' + eventTime,
            'short': True
    },
    {
    'title': 'IAM',
    'value': 'EventAction :' + Action +'\n' + 'Name :' + Name,
    'short': True
    }
    ]
    message_json = {
        'username': 'AWS Cloud Trail Infomation',
        'icon_emoji': ':awsicon:',
        'text': 'IAMの変更を検知しました',
        'attachments': [
        {
        'fallback': 'AWS CloudTrail Info',
        'color': 'warning',
        'title': Action,
        'fields': temp_message
        }
        ]
        }
    logger.info("Message: " + str(message_json))
    slacknotification(message_json)
    
def NSGnotifi(log2,eventTime,Action,user,message_json):
    temp_message = []
    Action = log2['eventName']
    items = log2['requestParameters']['ipPermissions']['items']
    if 'RevokeSecurityGroupIngress' in Action:
        Event = "NSGからIPが削除されました。"
    elif 'AuthorizeSecurityGroupIngress' in Action:
        Event = "NSGにIPが追加されました。"
    else:
        Event = Action
    for i in items:
        Port = str(i['fromPort'])
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
        temp_fields = [
                {
                "title":cidrIp,
                "value": "Description:" + description + '\n Port :' + Port,
                "short": "true"
                }
                ]
        temp_fields.extend(temp_fields)
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
            logger.info("Message: " + str(message_json))
            slacknotification(message_json)