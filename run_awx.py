"""import modules"""
import os
import json
import time
import traceback
import requests
import yaml

AWX_URL = "http://ansawx.xxx.zone:31642/api/v2/job_templates/32/launch/"
BEARER_TOKEN = os.getenv('BEARER_TOKEN_ENV')
#Job type check or run
JOB_TYPE = "check"

# Load the YAML file with task arguments
with open('arguments.yaml', 'r',encoding='utf-8') as file:
    tasks = yaml.safe_load(file)

#do basic checks for arguments file
for args in tasks:
    assert 'xstatus' in args
    assert args['xstatus'] == 0 or args['xstatus'] == 1
    assert 'full_fex_interface_number' in args
    assert 'vlans' in args or 'vlan_native' in args or 'port_profile_name_prior' in args
    assert len(args) <= 8 and len(args) > 2
    assert 'NET' in str(args['hostai'])
    assert 'port_profile_name_prior' not in args or ':' in args['port_profile_name_prior'] \
           or '-' in args['port_profile_name_prior'], \
           "If 'port_profile_name_prior' exists, it must contain a ':'"

#for later comparison
original_tasks = yaml.dump(tasks)

try:
    # Iterate over each task
    for task in tasks:
        if task['xstatus'] == 0:
            #print(task)
            # Construct the JSON payload
            payload = {
                "extra_vars": {
                    "hostai": task['hostai'],
                    "full_fex_interface_number": task['full_fex_interface_number'],
                    **({"full_fex_interface_number2": task['full_fex_interface_number2']} \
                    if 'full_fex_interface_number2' in task else {}),
                    **({"port_profile_name_prior": task['port_profile_name_prior']} \
                    if 'port_profile_name_prior' in task else {}),
                    **({"vlans": str(task['vlans']).replace(' ', '')} if 'vlans' in task else {}),
                    **({"native_vlan": str(task['vlan_native']).replace(' ', '')} \
                    if 'vlan_native' in task else {}),
                    **({"interface_description": task['interface_description']} \
                    if 'interface_description' in task else {})
                },
                "job_type": JOB_TYPE
            }

            # Make the API call
            response = requests.post(
                AWX_URL,
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {BEARER_TOKEN}"
                },
                data=json.dumps(payload)
            )

            # Handle the response
            if response.status_code == 201:
                if JOB_TYPE == "run":  # Update xstatus only if job type is 'run'
                    print("current status " + str(task['xstatus']) + " changing to xstatus to 1")
                    task['xstatus'] = 1
                response_data = json.loads(response.json()['extra_vars'])
                print((
                f"Job submitted for {task['full_fex_interface_number']} on {task['hostai']} "
                f"returned response with following args - hostai: {response_data['hostai']} "
                f"description: {response_data['interface_description']} "
                f"int1: {response_data['full_fex_interface_number']} "
                f"int2: {response_data['full_fex_interface_number2']} "
                f"port_profile: {response_data['port_profile_name_prior']} "
                f"vlans: {response_data['vlans']} vlan_native: {response_data['native_vlan']} "
                f"job_type: {response.json()['job_type']}"
                ))
                time.sleep(5)
            else:
                print("something not right with task provided: "+str(task))
                print("pinting output: " + str(response.json()))

except BaseException:
    traceback.print_exc()

# Compare the current tasks with the original
new_tasks = yaml.dump(tasks)

if original_tasks != new_tasks:
    print("Changes detected, writing to file.")
    with open("arguments.yaml", 'w',encoding='utf-8') as file:
        yaml.dump(tasks, file, default_flow_style=False)
else:
    print("No changes detected, skipping arguments file overwrite.")