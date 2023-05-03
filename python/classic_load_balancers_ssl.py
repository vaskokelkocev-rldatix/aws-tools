import json
import boto3
from datetime import datetime

REQUIRED_SSL_POLICY = "ELBSecurityPolicy-TLS13-1-2-Ext2-2021-06"
ACCEPTABLE_POLICIES = [
    "ELBSecurityPolicy-TLS13-1-2-Ext2-2021-06",
    "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"
]
IGNORED_LOAD_BALANCERS = ["asb-nhsp-legacy-test", "jenkins-lb-tf"]
READ_ONLY = True

# Create a Boto3 client for the AWS Elastic Load Balancing (ELB) service
elb_client = boto3.client('elb')

# Retrieve a list of all Application Load Balancers in the current AWS account
load_balancers = elb_client.describe_load_balancers()

pre_upgrade = {}
updated = {}
if READ_ONLY is True:
    print("Running in Read-Only mode")
else:
    print("Running in update mode. Changes will occure.")
    user_input = input("Do you wish to continue. (Y/N) [N]?")
    if user_input.lower() != 'y':
        exit()

# Iterate over each Application Load Balancer and print its name and SSL policy
for lb in load_balancers['LoadBalancerDescriptions']:
    lb_name = lb['LoadBalancerName']
    if lb_name in IGNORED_LOAD_BALANCERS:
        print(f"Ignoring Load Balancer: {lb_name}")
        continue
    # lb_arn = lb['LoadBalancerArn']
    # lb_listeners = elb_client.describe_listeners(LoadBalancerArn=lb_arn)
    for listener in lb['ListenerDescriptions']:
        print(lb_name, listener)
        continue
        if listener['Protocol'] == 'HTTPS':
            ssl_policy = listener['SslPolicy']
            lb_info = {
                "arn": lb_arn,
                "name": lb_name,
                "ssl_policy": ssl_policy
            }
            if ssl_policy not in pre_upgrade:
                pre_upgrade[ssl_policy] = [lb_info]
            else:
                pre_upgrade[ssl_policy].append(lb_info)

            # UPDATE_PROCESS
            if READ_ONLY is False and ssl_policy not in ACCEPTABLE_POLICIES:
                update = {
                    "name": lb_name,
                    "arn": lb_arn,
                    "listener_arn": listener['ListenerArn'],
                    "old_policy": ssl_policy,
                    "new_policy": REQUIRED_SSL_POLICY
                }
                updated[lb_name] = update
                elb_client.modify_listener(
                    ListenerArn=listener['ListenerArn'],
                    SslPolicy=REQUIRED_SSL_POLICY
                )
pre_upgrade_j = json.dumps(pre_upgrade)
updated_j = json.dumps(updated)

clb_list_files = "./output/clb_list_" + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.json'
pre_upgrade_file = './output/clb_pre_upgrade_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.json'
updated_file = './output/clb_updated_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.json'

with open(clb_list_files, 'w') as outfile:
    outfile.write(json.dumps(load_balancers, indent=4, sort_keys=True, default=str))

with open(pre_upgrade_file, 'w') as outfile:
    outfile.write(pre_upgrade_j)

with open(updated_file, 'w') as outfile:
    outfile.write(updated_j)
