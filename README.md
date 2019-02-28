# NSG_notification

* Notice to slack when NSG&IAM is changed
* It works with lambda of AWS.
* Cloudtrail →Clooudwatch→Lambda→slack
* Please use the following for Query.

## Clouwathc Filterling Query

```cloudwatch
>{(($.requestParameters.groupId = "********") || ($.requestParameters.groupId = "********")) && (($.eventName = AuthorizeSecurityGroupIngress) || ($.eventName = AuthorizeSecurityGroupEgress) || ($.eventName = RevokeSecurityGroupIngress) || ($.eventName = RevokeSecurityGroupEgress) || ($.eventName = DeleteSecurityGroup) || ($.eventName = UpdateSecurityGroup))|| (($.eventSource = "iam.amazonaws.com")) && ($.eventName != "Get*") && ($.eventName != "List*") && ($.eventName != "Describe*")}
```