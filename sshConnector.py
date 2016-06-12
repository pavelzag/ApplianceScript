import paramiko
token_id = ""
token = ""

def extract_token(string_to_cut):
    return string_to_cut.split("token-",1)[1][:-1]

def get_token(hostname, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, port=22, username=username, password=password)
    send_parameter = r"""oc get -n management-infra sa/management-admin --template='{{range .secrets}}{{printf "%s\n" .name}}{{end}}'"""
    stdin, stdout, stderr = ssh.exec_command(send_parameter)
    for line in stdout:
        if str(line).__contains__('token'):
            token_id = extract_token(line)
    command_begin = 'oc get -n management-infra secrets management-admin-token-' + token_id + ' --template'
    send_parameter = command_begin + r"""='{{.data.token}}' | base64 -d"""
    stdin, stdout, stderr = ssh.exec_command(send_parameter)
    for line in stdout:
        print('The token is: ' + line)
        token = line
    return token
# token = get_token(hostname='pavel-openshift-master01.scl.lab.tlv.redhat.com', port=22, username='root', password='qum5net')
# print(token)
# print('check')