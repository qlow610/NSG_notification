#NSG_notification

* Notice to slack when NSG is changed 

Clouwathc Filterling Query:

>{ (($.requestParameters.groupId = "********") || ($.requestParameters.groupId = "********")) && (($.eventName = AuthorizeSecurityGroupIngress) || ($.eventName = AuthorizeSecurityGroupEgress) || ($.eventName = RevokeSecurityGroupIngress) || ($.eventName = RevokeSecurityGroupEgress) || ($.eventName = DeleteSecurityGroup) || ($.eventName = UpdateSecurityGroup)) }

