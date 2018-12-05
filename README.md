#NSG_notification

* Notice to slack when NSG is changed 
* It works with lambda of AWS.
* Cloudtrail →Clooudwatch→Lambda→slack
* Please use the following for Query.

Clouwathc Filterling Query:

>{ (($.requestParameters.groupId = "********") || ($.requestParameters.groupId = "********")) && (($.eventName = AuthorizeSecurityGroupIngress) || ($.eventName = AuthorizeSecurityGroupEgress) || ($.eventName = RevokeSecurityGroupIngress) || ($.eventName = RevokeSecurityGroupEgress) || ($.eventName = DeleteSecurityGroup) || ($.eventName = UpdateSecurityGroup)) }

