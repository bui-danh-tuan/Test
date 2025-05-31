import http.client
import json

conn = http.client.HTTPSConnection("google.serper.dev")
payload = json.dumps({
  "q": "Hỗ trợ đăng ký học phần và lịch học. site:uet.vnu.edu.vn"
})
headers = {
  'X-API-KEY': '',
  'Content-Type': 'application/json'
}
conn.request("POST", "/search", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))