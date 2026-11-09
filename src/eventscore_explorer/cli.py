import argparse
import json
from dataclasses import asdict
from pathlib import Path
from .core import load_csv, evaluate

def report(truth,predictions,tolerances):
    payload=json.dumps({'truth':[asdict(x) for x in truth], 'predictions':[asdict(x) for x in predictions],
                        'results':[evaluate(truth,predictions,x) for x in tolerances]},ensure_ascii=True).replace('<','\\u003c')
    return TEMPLATE.replace('__DATA__',payload)

def main(argv=None):
    p=argparse.ArgumentParser(description='Explain one-to-one event matching; CSV times in seconds.')
    p.add_argument('truth'); p.add_argument('predictions')
    p.add_argument('--tolerances',default='0,0.5,1,2',help='Comma-separated nonnegative endpoint tolerances (seconds)')
    p.add_argument('--output',default='eventscore.html'); p.add_argument('--json',dest='json_output')
    args=p.parse_args(argv)
    try:
        truth,predictions=load_csv(args.truth),load_csv(args.predictions)
        tolerances=sorted(set(float(x) for x in args.tolerances.split(',')))
        outputs=[Path(args.output)]+([Path(args.json_output)] if args.json_output else [])
        inputs={Path(args.truth).resolve(),Path(args.predictions).resolve()}
        if len({x.resolve() for x in outputs}) != len(outputs) or any(x.resolve() in inputs or x.exists() for x in outputs):
            raise ValueError('Outputs must be distinct new files, separate from inputs')
        html=report(truth,predictions,tolerances)
        for x in outputs: x.parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(html,encoding='utf-8')
        if args.json_output:
            Path(args.json_output).write_text(json.dumps([evaluate(truth,predictions,x) for x in tolerances],indent=2),encoding='utf-8')
        print(f'Report: {args.output}')
        return 0
    except (ValueError,OSError,KeyError) as e:
        p.exit(2,f'Error: {e}\n')

TEMPLATE=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EventScore Explorer</title>
<style>body{font:16px system-ui;background:#f5f7fb;color:#18273b;margin:0}main{max-width:1100px;margin:auto;padding:40px 24px}h1{font-size:32px;margin:8px 0}header p{max-width:780px;color:#536175}section{background:white;border:1px solid #dce3ed;border-radius:12px;padding:24px;margin:20px 0}select{font:inherit;padding:8px}#metrics{display:flex;flex-wrap:wrap;gap:28px;margin-top:24px}.metric b{display:block;font-size:30px}small,.muted{color:#536175}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:12px;border-bottom:1px solid #e1e7ef}svg{width:100%;min-width:650px}button{font:inherit;padding:9px 16px;cursor:pointer}.scroll{overflow:auto}.tag{font-size:12px;letter-spacing:2px;color:#285aaa}li{margin:8px 0}</style>
<main><header><div class="tag">TIME SERIES · EVALUATION LAB</div><h1>EventScore Explorer</h1><p>See which events matched, what was missed, and how an endpoint tolerance changes the result. Synthetic demo or your own CSV — all processing for this report is local.</p></header>
<section><label for="tolerance">Endpoint tolerance (seconds) </label><select id="tolerance"></select><div id="metrics"></div><p class="muted">One-to-one maximum-cardinality matching. Labels and recordings must agree. At zero tolerance, touching endpoints do not overlap. Signed onset offset = prediction start − truth start; negative means early.</p></section>
<section><h2>Event timeline</h2><p>Blue: ground truth · Green: matched prediction · Orange: unmatched prediction. Each event has its own row; times are relative to the recording.</p><div class="scroll" id="timeline"></div></section>
<section><h2>Why these events matched</h2><div class="scroll"><table><thead><tr><th>Truth</th><th>Prediction</th><th>Rule</th><th>Overlap (s)</th><th>Onset offset (s)</th></tr></thead><tbody id="pairs"></tbody></table></div><h3>Unmatched events</h3><ul id="unmatched"></ul><p id="ambiguity"></p><button id="download">Download evaluation JSON</button></section>
<footer>Prototype 0.1 · No true-negative count, specificity, or false alarms/hour is inferred without recording duration. Matching maximizes count, not temporal quality. This is an explicit evaluation policy, not a clinical standard.</footer></main>
<script type="application/json" id="data">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent), select=document.getElementById('tolerance');
data.results.forEach((r,i)=>{const o=document.createElement('option');o.value=i;o.textContent=r.tolerance_seconds;select.append(o)});
function cell(row,value){const td=document.createElement('td');td.textContent=value;row.append(td)}
function render(){const r=data.results[Number(select.value)],m=document.getElementById('metrics');m.replaceChildren();
for(const [name,value] of [['Matched',r.tp],['False alarms',r.fp],['Missed',r.fn],['Precision',r.precision],['Recall',r.recall],['F1',r.f1]]){const box=document.createElement('div');box.className='metric';const b=document.createElement('b');b.textContent=value===null?'N/A':(name==='Precision'||name==='Recall'||name==='F1'?value.toFixed(3):value);box.append(b,document.createTextNode(name));m.append(box)}
const pairs=document.getElementById('pairs');pairs.replaceChildren();r.matches.forEach(p=>{const tr=document.createElement('tr');[p.truth,p.prediction,p.reason,p.overlap_seconds.toFixed(3),p.onset_offset_seconds.toFixed(3)].forEach(x=>cell(tr,x));pairs.append(tr)});
const ul=document.getElementById('unmatched');ul.replaceChildren();for(const [items,kind] of [[r.missed,'Missed'],[r.false_alarms,'False alarm']])for(const x of items){const li=document.createElement('li');li.textContent=kind+' · '+x.id+' — '+x.reason;ul.append(li)}if(!ul.children.length){const li=document.createElement('li');li.textContent='No unmatched events';ul.append(li)}
document.getElementById('ambiguity').textContent=r.ambiguous_truth.length?'Multiple eligible predictions: '+r.ambiguous_truth.join(', ')+'. Pair identities and onset offsets can depend on deterministic tie-breaking.':'No truth event has multiple eligible predictions.';
const host=document.getElementById('timeline');host.replaceChildren(); const ns='http://www.w3.org/2000/svg'; const records=[...new Set([...data.truth,...data.predictions].map(x=>x.recording))];
for(const record of records){const title=document.createElement('h3');title.textContent=record;host.append(title);const events=[...data.truth.filter(x=>x.recording===record).map(x=>({...x,kind:'truth'})),...data.predictions.filter(x=>x.recording===record).map(x=>({...x,kind:'prediction'}))]; const end=Math.max(1,...events.map(e=>e.end));const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 1000 ${events.length*34+45}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Event intervals for '+record+' in seconds');function text(x,y,s){const n=document.createElementNS(ns,'text');n.setAttribute('x',x);n.setAttribute('y',y);n.setAttribute('font-size','13');n.textContent=s;svg.append(n)}text(260,20,'0 s');text(900,20,end.toFixed(2)+' s');events.forEach((e,i)=>{const y=35+i*34;text(0,y+17,e.kind+' '+e.id+' ['+e.label+']');const rect=document.createElementNS(ns,'rect');rect.setAttribute('x',260+e.start/end*680);rect.setAttribute('y',y);rect.setAttribute('width',Math.max(2,(e.end-e.start)/end*680));rect.setAttribute('height',22);rect.setAttribute('rx',3);rect.setAttribute('fill',e.kind==='truth'?'#386bc0':r.matches.some(p=>p.prediction===e.id)?'#168579':'#c5682a');const tip=document.createElementNS(ns,'title');tip.textContent=e.start+'–'+e.end+' seconds';rect.append(tip);svg.append(rect)});host.append(svg)} }
select.addEventListener('change',render);document.getElementById('download').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(data.results[Number(select.value)],null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='eventscore-evaluation.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};render();
</script></html>'''
