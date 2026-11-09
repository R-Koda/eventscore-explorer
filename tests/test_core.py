import unittest
from eventscore_explorer.core import Event as E, evaluate
from eventscore_explorer.cli import report
class EvaluationTests(unittest.TestCase):
 def test_half_open_and_tolerance(self):
  t=[E('t',1,2)];p=[E('p',2,3)]
  self.assertEqual(evaluate(t,p)['tp'],0)
  self.assertEqual(evaluate(t,p,0.01)['tp'],1)
 def test_augmenting_path_beats_greedy(self):
  t=[E('t1',0,10),E('t2',2,3)];p=[E('p1',2,3),E('p2',8,9)]
  r=evaluate(t,p);self.assertEqual(r['tp'],2)
  self.assertEqual({(x['truth'],x['prediction']) for x in r['matches']},{('t1','p2'),('t2','p1')})
 def test_no_cross_recording_or_label(self):
  self.assertEqual(evaluate([E('t',1,3)],[E('p',1,3,recording='other'),E('q',1,3,label='other')],100)['tp'],0)
 def test_duplicate_prediction_is_false_alarm(self):
  r=evaluate([E('t',1,4)],[E('p',1,3),E('q',2,4)])
  self.assertEqual((r['tp'],r['fp'],r['fn']),(1,1,0))
 def test_empty_is_not_perfect(self):
  r=evaluate([],[]);self.assertIsNone(r['precision']);self.assertIsNone(r['recall']);self.assertIsNone(r['f1'])
 def test_reject_invalid(self):
  for a,b in [(1,1),(-1,1),(0,float('inf'))]:
   with self.assertRaises(ValueError):E('x',a,b)
  with self.assertRaises(ValueError):evaluate([],[],float('nan'))
  with self.assertRaises(ValueError):evaluate([E('x',0,1),E('x',2,3)],[])
 def test_deterministic_and_injection_safe(self):
  t=[E('t',1,4)];p=[E('</script><script>alert(1)</script>',1,2),E('p',2,3)]
  self.assertEqual(evaluate(t,p),evaluate(t,list(reversed(p))))
  self.assertNotIn('</script><script>alert',report(t,p,[0]))
if __name__=='__main__':unittest.main()
