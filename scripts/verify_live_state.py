import urllib.request, urllib.parse, json

data = urllib.parse.urlencode({'username': 'admin', 'password': 'Admin@SentinelX2026'}).encode()
req = urllib.request.Request('http://localhost:8888/api/auth/login', data=data, method='POST')
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']
headers = {'Authorization': f'Bearer {token}'}

def get(path):
    r = urllib.request.Request(f'http://localhost:8888/api{path}', headers=headers)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read().decode())

stats = get('/overview/stats')
print('=== OVERVIEW STATS ===')
print('Total Events:', stats['total_events'])
print('Total Findings:', stats['total_findings'])
print('Total Incidents:', stats['total_incidents'])
print('Severity Dist:', stats['severity_distribution'])

events = get('/events?limit=10')
print('=== EVENTS RETRIEVED ===', len(events))
for ev in events[:3]:
    print(f" - Event: {ev['event_id']} | type: {ev['event_type']} | host: {ev.get('host_id')} | user: {ev.get('user_id')} | src_ip: {ev.get('src_ip')}")

incidents = get('/incidents')
print('=== INCIDENTS RETRIEVED ===', len(incidents))
for inc in incidents:
    inc_id = inc['id']
    print(f" - Incident: {inc_id} | sev: {inc['severity']} | title: {inc['title']} | findings: {inc['findings_count']} | risk: {inc['graph_risk_score']}")
    detail = get(f"/incidents/{inc_id}")
    print(f"   -> detail findings: {len(detail['findings'])} | evidence events: {len(detail['evidence_events'])}")
    graph = get(f"/graph/incident/{inc_id}")
    print(f"   -> graph nodes: {graph['node_count']} | edges: {graph['edge_count']}")
    for node in graph['nodes'][:3]:
        print(f"      Node: {node['label']} ({node['type']}) risk={node['risk_score']}")
