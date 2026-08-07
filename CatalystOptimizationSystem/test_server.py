import threading, http.client, json
from http.server import HTTPServer
from CatalystOptimizationSystem.api.app import Handler

port = 8201
server = HTTPServer(('127.0.0.1', port), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

boundary = '----WebKitFormBoundaryABC123'
file_content = b'col1,col2\n1,2\n3,4'
filename = 'test.csv'
parts = [
    f'--{boundary}\r\n'.encode(),
    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
    b'Content-Type: text/csv\r\n\r\n',
    file_content,
    b'\r\n',
    f'--{boundary}--\r\n'.encode()
]
body = b''.join(parts)
headers = {
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'Content-Length': str(len(body))
}
conn = http.client.HTTPConnection('127.0.0.1', port)
conn.request('POST', '/upload', body, headers)
resp = conn.getresponse()
print('upload status', resp.status)
resp_data = resp.read()
print(resp_data.decode())
info = json.loads(resp_data)
path = info['path']

payload = json.dumps({'csv_path': path, 'row_index': 0}).encode()
headers = {'Content-Type': 'application/json', 'Content-Length': str(len(payload))}
conn.request('POST','/record',payload,headers)
resp = conn.getresponse()
print('record status', resp.status)
print(resp.read().decode())

server.shutdown()
