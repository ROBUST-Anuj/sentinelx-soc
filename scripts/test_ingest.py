import urllib.request, urllib.parse, json

# 1. Login
data = urllib.parse.urlencode({'username': 'admin', 'password': 'Admin@SentinelX2026'}).encode()
req = urllib.request.Request('http://localhost:8888/api/auth/login', data=data, method='POST')
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']

# 2. Synthetic syslog with 6 brute force ssh attempts + 1 successful sudo elevation
lines = [
    'Oct 12 14:00:01 ubuntu-srv sshd[1024]: Failed password for invalid user admin from 198.51.100.24 port 44321 ssh2',
    'Oct 12 14:00:02 ubuntu-srv sshd[1025]: Failed password for invalid user admin from 198.51.100.24 port 44322 ssh2',
    'Oct 12 14:00:03 ubuntu-srv sshd[1026]: Failed password for invalid user admin from 198.51.100.24 port 44323 ssh2',
    'Oct 12 14:00:04 ubuntu-srv sshd[1027]: Failed password for invalid user admin from 198.51.100.24 port 44324 ssh2',
    'Oct 12 14:00:05 ubuntu-srv sshd[1028]: Failed password for invalid user admin from 198.51.100.24 port 44325 ssh2',
    'Oct 12 14:00:06 ubuntu-srv sshd[1029]: Failed password for invalid user admin from 198.51.100.24 port 44326 ssh2',
    'Oct 12 14:00:07 ubuntu-srv sudo: jdoe : TTY=pts/0 ; PWD=/home/jdoe ; USER=root ; COMMAND=/bin/bash'
]
log_content = '\n'.join(lines)

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
parts = [
    f'--{boundary}\r\nContent-Disposition: form-data; name="source_type"\r\n\r\nlinux_auth\r\n',
    f'--{boundary}\r\nContent-Disposition: form-data; name="source_name"\r\n\r\nsensor-edge-01\r\n',
    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="auth.log"\r\nContent-Type: text/plain\r\n\r\n{log_content}\r\n',
    f'--{boundary}--\r\n'
]
body = ''.join(parts).encode('utf-8')

req = urllib.request.Request('http://localhost:8888/api/ingestion/upload', data=body, method='POST')
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

resp = urllib.request.urlopen(req)
res_json = json.loads(resp.read().decode())
print('INGESTION RESULT:', json.dumps(res_json, indent=2))
