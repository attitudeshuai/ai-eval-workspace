import json, os, sys, glob, re
sys.stdout.reconfigure(encoding='utf-8')

WS = os.path.abspath('.')
base = 'deliverables/cc-solo/session-0909'
REC = os.path.join(WS, 'sessions', 'cc-solo', 'session-0909', 'records')
cache = json.load(open('projects/cc-solo/.solo_session.json', encoding='utf-8'))
S = 'https://solo2.jzxhnh.com/api/v1/submissions'


def get(url):
    import urllib.request
    req = urllib.request.Request(url, headers={
        'Cookie': cache['cookie'], 'X-CSRF-Token': cache['csrf'], 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def blocks(text):
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r'^##\s+(.*?)\s*$', line)
        if m:
            if cur is not None:
                out[cur] = '\n'.join(buf).strip()
            cur, buf = m.group(1), []
        else:
            buf.append(line)
    if cur is not None:
        out[cur] = '\n'.join(buf).strip()
    return out


sess_of = {}
for info in glob.glob(os.path.join(REC, '**', 'task-info.md'), recursive=True):
    task = os.path.basename(os.path.dirname(info))
    m = re.search(r'##\s*SessionID\s*\n+([^\n]+)', open(info, encoding='utf-8').read())
    if m:
        sess_of[task] = m.group(1).strip()

rec_index = {}
for p in glob.glob(os.path.join(REC, '**', '*-R*.md'), recursive=True):
    m = re.match(r'(.+)-R(\d+)\.md$', os.path.basename(p))
    if not m:
        continue
    b = blocks(open(p, encoding='utf-8').read())
    rec_index[(sess_of.get(m.group(1), ''), (b.get('TurnID/PromptID') or '').strip(), int(m.group(2)))] = {
        'task': m.group(1), 'round': int(m.group(2)), 'path': p, 'b': b,
    }

items, page = [], 1
while True:
    d = get('%s?page=%d&page_size=100&stage=&keyword=&date_from=&date_to=&user_id=0' % (S, page))
    items.extend(d.get('items') or [])
    if page >= int((d.get('meta') or {}).get('total_pages') or 1):
        break
    page += 1
win = sorted([i for i in items if 'cc-solo-cc-' in (i.get('repo_id') or '')
              and i.get('status') == 'PENDING_FIX'], key=lambda x: int(x['id']))

out = []
for i in win:
    sid = int(i['id'])
    p = os.path.join(base, 'submission-%d-detail.json' % sid)
    d = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else get('%s/%d' % (S, sid))
    if not os.path.exists(p):
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    loc = rec_index.get((d.get('session_id'), d.get('turn_id'), d.get('round_no')))
    out.append({'id': sid, 'detail': d, 'loc': loc})

print('Windows 待返修 %d 条\n' % len(out))
for o in out:
    d, loc = o['detail'], o['loc']
    print('=' * 110)
    print('#%d  %s  轮次=%s  v%s  本地=%s' % (
        o['id'], d.get('question_type'), d.get('round_no'), d.get('current_version'),
        ('%s-R%02d  %s' % (loc['task'], loc['round'], os.path.relpath(loc['path'], WS))) if loc else '（无记录）'))
    print('--- 打回原因全文 ---')
    print((d.get('qc_summary') or '').strip())
    if loc:
        print('--- 本轮五维（分数 / 描述）---')
        b = loc['b']
        for dim in ['交付完整性', '指令遵循', '任务规划', '推理能力', '执行能力']:
            print('[%s] %s' % (dim, b.get(dim)))
            print(b.get(dim + '-描述', ''))
            print()

json.dump([{'id': o['id']} for o in out], open('.tmp_win_ids.json', 'w'), ensure_ascii=False)
