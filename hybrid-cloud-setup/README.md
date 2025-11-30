# Ansible Windows Setup Guide

You are seeing Ansible errors because the target Windows VM is not configured for remote management with Ansible. This guide will walk you through the steps to fix this.

## 1. Configure WinRM on the Windows VM

You need to run the `ConfigureRemotingForAnsible.ps1` script on your Windows VM to enable Ansible to connect to it.

1.  Open PowerShell **as an Administrator** on your Windows VM.
2.  Navigate to the `hybrid-cloud-setup` directory.
3.  Run the following command:

```powershell
powershell.exe -ExecutionPolicy ByPass -File .\ConfigureRemotingForAnsible.ps1
```

This will configure WinRM on the Windows VM.

## 2. Correct your Ansible `hosts.ini` file

The `hosts.ini` file you were using has a formatting error. From your Proxmox host, create the `hosts.ini` file in the `/root/ansible_setup` directory with the following content:

```ini
[windows_vms]
192.168.1.181

[windows_vms:vars]
ansible_user=Administrator
ansible_password=YourPassword
ansible_connection=winrm
ansible_winrm_server_cert_validation=ignore
```

**Note:** Replace `YourPassword` with the actual password for the Administrator account.

## 3. Re-run the Ansible Playbook

Now, from your Proxmox host, run the Ansible playbook again:

```bash
cd /root/ansible_setup
ansible-playbook -i hosts.ini setup-ai-workstation.yml
```

This should now successfully connect to the Windows VM and run the playbook.
