import json
import boto3
from datetime import datetime

REQUIRED_SSL_POLICY = "ELBSecurityPolicy-TLS13-1-2-Ext2-2021-06"
ACCEPTABLE_POLICIES = ["ELBSecurityPolicy-TLS13-1-2-Ext2-2021-06"]
IGNORED_LOAD_BALANCERS = ["asb-nhsp-legacy-test", "jenkins-lb-tf"]
READ_ONLY = True

# Create a Boto3 client for the AWS Elastic Load Balancing (ELB) service
elbv2_client = boto3.client('elbv2')

# Retrieve a list of all Application Load Balancers in the current AWS account
load_balancers = elbv2_client.describe_load_balancers(PageSize=400)

pre_upgrade = {}
updated = {}
if READ_ONLY is True:
    print("Running in Read-Only mode")
else:
    print("Running in update mode. Changes will occure.")
    user_input = input("Do you wish to continue. (Y/N) [N]? ")
    if user_input.lower() != 'y':
        exit()

# Iterate over each Application Load Balancer and print its name and SSL policy
print(f"Found loadbalancers {len(load_balancers['LoadBalancers'])}")
for lb in load_balancers['LoadBalancers']:
    lb_name = lb['LoadBalancerName']
    if lb_name in IGNORED_LOAD_BALANCERS:
        print(f"Ignoring Load Balancer: {lb_name}")
        continue
    lb_arn = lb['LoadBalancerArn']
    lb_listeners = elbv2_client.describe_listeners(LoadBalancerArn=lb_arn)
    for listener in lb_listeners['Listeners']:
        if listener['Protocol'] in ['HTTPS', 'TLS']:
            ssl_policy = listener['SslPolicy']
            lb_info = {"arn": lb_arn, "name": lb_name, "ssl_policy": ssl_policy}
            if ssl_policy not in pre_upgrade:
                pre_upgrade[ssl_policy] = [lb_info]
            else:
                pre_upgrade[ssl_policy].append(lb_info)

            # UPDATE PROCESS
            if READ_ONLY is False and ssl_policy not in ACCEPTABLE_POLICIES:
                update = {
                    "name": lb_name,
                    "arn": lb_arn,
                    "listener_arn": listener['ListenerArn'],
                    "old_policy": ssl_policy,
                    "new_policy": REQUIRED_SSL_POLICY
                }
                if lb_name not in updated:
                    updated[lb_name] = update
                else:
                    updated[lb_name].append(update)
                elbv2_client.modify_listener(
                    ListenerArn=listener['ListenerArn'],
                    SslPolicy=REQUIRED_SSL_POLICY
                )
        else:
            print(f"Ignoring protocol {listener['Protocol']} on listener {listener['ListenerArn']}")
pre_upgrade_j = json.dumps(pre_upgrade, indent=4, sort_keys=True, default=str)
updated_j = json.dumps(updated, indent=4, sort_keys=True, default=str)

alb_list_files = "./output/alb_list_" + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.json'
pre_upgrade_file = './output/alb_pre_upgrade_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.json'
updated_file = './output/alb_updated_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.json'

with open(alb_list_files, 'w') as outfile:
    outfile.write(json.dumps(load_balancers, indent=4, sort_keys=True, default=str))

with open(pre_upgrade_file, 'w') as outfile:
    outfile.write(pre_upgrade_j)

with open(updated_file, 'w') as outfile:
    outfile.write(updated_j)
