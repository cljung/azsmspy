#!/usr/bin/python 
import os
import sys
import getpass
import json
import time
from pprint import pprint
from azure import *
from azure.servicemanagement import *

#-------------------------------------------------------------------------
with open('azure-config.json') as cfg_file:    
    cfg = json.load(cfg_file)

sms = ServiceManagementService(cfg["subscriptionid"], cfg["certificate"])

#-------------------------------------------------------------------------
def wait_for_async(request_id, operation_name, timeout): 
     count = 0 
     result = sms.get_operation_status(request_id) 
     while result.status == 'InProgress': 
         count = count + 1 
         if count > timeout: 
             print('Timed out waiting for async operation to complete.') 
             return 
         time.sleep(10) 
         result = sms.get_operation_status(request_id) 
         print(vars(result))
         if result.error: 
             print(result.error.code) 
             print(vars(result.error)) 
     print(result.status) 
     print(operation_name + ' took: ' + str(count*10) + 's')  

#-------------------------------------------------------------------------
def wait_vm_to_start( cs_name, depl_name, timeout ): 
     count = 0 
     result = sms.get_deployment_by_name(service_name=cs_name, deployment_name=depl_name)
     while result.role_instance_list[0].instance_status != 'ReadyRole': 
         count = count + 1 
         if count > timeout: 
             print('Timed out waiting for vm to start.') 
             return 
         time.sleep(30) 
         result = sms.get_deployment_by_name(service_name=cs_name, deployment_name=depl_name) 
     print( 'vm running - took: ' + str(count*30) + 's')  
     print( 'ipaddr: ' + result.virtual_ips[0].address )  

#-------------------------------------------------------------------------
def CreateDeployment():
    password = cfg["password"]
    if password=="*" or password=="":
         password = getpass.getpass("Enter password for user " + cfg["userid"] + ": ")
         
    print('Creating Cloud Service ' + cfg["name"] + " in " + cfg["location"])
    sms.create_hosted_service(service_name=cfg["name"], label=cfg["name"], location=cfg["location"])

    count = 0
    for vm in cfg["vm"]:
        count = count + 1
        print('Creating VM ' + vm["vmname"])

        # Network subnet and endpoints (not ILB'd)
        network_cfg = ConfigurationSet()
        network_cfg.configuration_set_type = 'NetworkConfiguration'
        network_cfg.subnet_names.append(cfg["subnet"])        
        for endpoint in vm["endpoints"]:
            print('Endpoint ' + endpoint["name"] + " " + endpoint["protocol"] + " " + endpoint["port"] + " <-> " + endpoint["local_port"])
            network_cfg.input_endpoints.input_endpoints.append(
                     ConfigurationSetInputEndpoint(name=endpoint["name"],
                                              protocol=endpoint["protocol"],
                                              port=endpoint["port"],
                                              local_port=endpoint["local_port"]))

        # Destination storage account container/blob where the VM disk will be created
        media_link = 'https://' + cfg["storageaccount"] + '.blob.core.windows.net/vhds/' + vm["vmname"] + '_osdisk.vhd'
        os_hd = OSVirtualHardDisk(cfg["imagename"], media_link)

        # Linux VM configuration options
        linux_config = LinuxConfigurationSet( host_name=vm["vmname"], 
                                              user_name=cfg["userid"], user_password=password,
                                              disable_ssh_password_authentication=False)
        linux_config.ssh = None

        # provision VMs - different 1st vs 2..n
        if count == 1:  
           result = sms.create_virtual_machine_deployment(
                service_name=cfg["name"],
                deployment_name=cfg["name"],
                deployment_slot=cfg["deploymentslot"],
                label=vm["vmname"],
                role_name=vm["vmname"],
                system_config=linux_config,
                os_virtual_hard_disk=os_hd,
                role_size=cfg["vmsize"],
                network_config=network_cfg,
                virtual_network_name = cfg["vnetname"]
                )
        else:
            result = sms.add_role(
                service_name=cfg["name"],
                deployment_name=cfg["name"],
                role_name=vm["vmname"],
                system_config=linux_config,
                os_virtual_hard_disk=os_hd,
                role_size=cfg["vmsize"],
                network_config=network_cfg
                )
        wait_for_async(result.request_id, 'Create VM ' + vm["vmname"], 600)

    # wait for the 1st VM to start
    print('waiting for vm to start...')
    wait_vm_to_start( cfg["name"], cfg["name"], 600 )

#-------------------------------------------------------------------------
def DeleteDeployment():        
    print('Deleting ' + cfg["name"])
    try:
        result = sms.delete_deployment(cfg["name"], cfg["name"], delete_vhd=True)
        wait_for_async(result.request_id, 'Delete Deployment ' + cfg["name"], 600)
    except:
        print('No Deployment')

    try:
         result = sms.delete_hosted_service(cfg["name"], complete=True);
         wait_for_async(result.request_id, 'Delete Cloud Service ' + cfg["name"], 600)
    except:
         print('No Cloud Service')
         
#-------------------------------------------------------------------------
def GetDeployment():        
    print('Get Deployment ' + cfg["name"])
    try:
         result = sms.get_deployment_by_name(service_name=cfg["name"], deployment_name=cfg["name"])
         #print(vars(result))
         print(result.status)
         print(result.virtual_ips[0].address)
         print(result.role_instance_list[0].instance_status)
         #print(vars(result.role_instance_list[0]))
    except:
         print('No Cloud Service')
         
#-------------------------------------------------------------------------
action = "get"

if len(sys.argv) >= 2:
     action = sys.argv[1]

if action == "get":
    GetDeployment()

if action == "delete":
    DeleteDeployment()

if action == "create":
    CreateDeployment()

