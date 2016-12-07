# Create a Classic VM in Azure using Python SDK

This sample creates a classic VM in Azure using the old (and depricated) Azure Python SDK. 
It is depricated since the way forward is ARM and this means that it's not maintained any more.
However, if you still have classic VMs and need to script creating them, the legacy Python SDK might be what you are looking for.

In Mac/Linux environment, most scripting is done with bash and Azure CLI, but if you are a Python guy (or just don't like Azure CLI), this sample can be useful.

## Config file

The config file is in json format and contains all settings for creating the VM. There you specify the name of the Cloude Service, the VM and the Storage Account where you will store the VHD file.
My sample assumes that the VM will be provisioned into a Virtual Network, and you need to specify the VNet and the subnet name.

The imagename value is the name of the base os image that you will use and you can find this using the "azure vm image list" Azure CLI command.

The subscriptionid is the Azure Subscription that the VM should be provisioned to and that guid you can grab via the "azure account show" Azure CLI command.

Finally, using the Classic model in Azure means that you must use a management certificate. You need to generate a self signed certificate and upload that in the classic portal,
https://manage.windowsazure.com, in the Settings > MANAGEMENT CERTIFICATES section. There you need to upload a .cer file. On the client side you must have the same certificate in the PEM-file format.
Yes, I know, it would be easier to use the same format, but get over it and just create the cert in different file formats.

Instructions for generating a cert exits on the below github page

## Downloading the Azure Python SDK

You can find the Clasic Azure Python SDK here https://github.com/Azure/azure-sdk-for-python/tree/master/azure-servicemanagement-legacy
Installing it on Mac/linux is done via the command 
<pre><code>
pip install azure-servicemanagement-legacy
</code></pre>

## Running the Python code

The python code can create a classic VM, delete it and get some of its status. After updating the json config file, you invoke the script like below

<pre><code>
python azure-vm-create.py create
</code></pre>

The script creates the VM, waits until the VM is in Running mode and outputs its ip address.


