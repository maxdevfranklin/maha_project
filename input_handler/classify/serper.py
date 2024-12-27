import http.client
import json

conn = http.client.HTTPSConnection("google.serper.dev")
payload = json.dumps({
  "q": "maha movement"
})
headers = {
  'X-API-KEY': '0bd98d7e73354be21cd65a9e91f0affb53cb3774',
  'Content-Type': 'application/json'
}
conn.request("POST", "/search", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))