"""Explicit, deterministic maximum-cardinality interval matching (not clinical scoring)."""
import csv
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Event:
    id: str
    start: float
    end: float
    label: str = 'event'
    recording: str = 'default'

    def __post_init__(self):
        if not self.id or not self.label or not self.recording:
            raise ValueError('id, label and recording must not be empty')
        if not math.isfinite(self.start) or not math.isfinite(self.end) or self.start < 0 or self.end <= self.start:
            raise ValueError(f'{self.id}: require finite 0 <= start < end (seconds)')

def load_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not {'id', 'start', 'end'} <= set(reader.fieldnames or []):
            raise ValueError('CSV requires id,start,end; optional label,recording')
        return validate([Event(r['id'], float(r['start']), float(r['end']), r.get('label', 'event'), r.get('recording', 'default')) for r in reader])

def validate(events):
    events = list(events)
    if len({e.id for e in events}) != len(events):
        raise ValueError('Event IDs must be unique within each input')
    return events

def evaluate(truth, predictions, tolerance=0.0):
    """Overlap of half-open intervals OR positive tolerance covering endpoint gap.

    One prediction matches at most one truth. Maximum-cardinality bipartite
    matching, deterministic sorted traversal; not a minimum-delay assignment.
    Tolerance never crosses recording or label boundaries.
    """
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('tolerance must be finite and nonnegative')
    truth = sorted(validate(truth), key=lambda e: (e.recording,e.label,e.start,e.end,e.id))
    predictions = sorted(validate(predictions), key=lambda e: (e.recording,e.label,e.start,e.end,e.id))
    if len(truth) > 2000 or len(predictions) > 2000:
        raise ValueError('Prototype supports at most 2000 events per input')
    def eligible(t,p):
        if (t.recording,t.label) != (p.recording,p.label):
            return False
        overlap = min(t.end,p.end)-max(t.start,p.start)
        gap = max(t.start-p.end,p.start-t.end,0)
        return overlap > 0 or (tolerance > 0 and gap <= tolerance)
    edges = [[j for j,p in enumerate(predictions) if eligible(t,p)] for t in truth]
    # Iterative augmenting paths avoid recursion depth failures on long graphs.
    owner = {}
    for start in range(len(truth)):
        queue = [start]; seen_t = {start}; parent_p = {}; free = None
        for i in queue:
            for j in edges[i]:
                if j in parent_p:
                    continue
                parent_p[j] = i
                if j not in owner:
                    free = j
                    break
                nxt = owner[j]
                if nxt not in seen_t:
                    seen_t.add(nxt); queue.append(nxt)
            if free is not None:
                break
        if free is not None:
            inverse = {i:j for j,i in owner.items()}
            while True:
                i = parent_p[free]
                old = inverse.get(i)
                owner[free] = i
                if old is None:
                    break
                free = old
    pairs=[]
    for j,i in sorted(owner.items(),key=lambda x:x[1]):
        t,p = truth[i],predictions[j]
        overlap = max(0,min(t.end,p.end)-max(t.start,p.start))
        pairs.append({'truth':t.id,'prediction':p.id,'reason':'overlap' if overlap else 'within tolerance',
                      'overlap_seconds':overlap,'gap_seconds':max(t.start-p.end,p.start-t.end,0),
                      'onset_offset_seconds':p.start-t.start})
    tp=len(pairs); fp=len(predictions)-tp; fn=len(truth)-tp
    return {'tolerance_seconds':tolerance,'tp':tp,'fp':fp,'fn':fn,
            'precision':tp/len(predictions) if predictions else None,
            'recall':tp/len(truth) if truth else None,
            'f1':2*tp/(len(truth)+len(predictions)) if truth or predictions else None,
            'matches':pairs,
            'missed':[{'id':t.id,'reason':'candidate assigned to another event' if edges[i] else 'no eligible prediction'} for i,t in enumerate(truth) if i not in owner.values()],
            'false_alarms':[{'id':p.id,'reason':'candidate assigned to another event' if any(j in e for e in edges) else 'no eligible truth'} for j,p in enumerate(predictions) if j not in owner],
            'ambiguous_truth':[truth[i].id for i,e in enumerate(edges) if len(e)>1]}
