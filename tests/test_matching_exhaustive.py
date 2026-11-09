import random
import unittest
from eventscore_explorer.core import Event,evaluate

class ExhaustiveOracleTests(unittest.TestCase):
    def test_matches_exhaustive_small_graphs(self):
        rng=random.Random(12)
        for trial in range(300):
            truth=[Event(f't{i}',a:=rng.randrange(10),a+rng.randrange(1,6)) for i in range(4)]
            predictions=[Event(f'p{i}',a:=rng.randrange(10),a+rng.randrange(1,6)) for i in range(4)]
            edges=[[j for j,b in enumerate(predictions) if min(a.end,b.end)>max(a.start,b.start)] for a in truth]
            def oracle(i,used):
                if i==len(truth): return 0
                return max([oracle(i+1,used)]+[1+oracle(i+1,used|{j}) for j in edges[i] if j not in used])
            with self.subTest(trial=trial):
                self.assertEqual(evaluate(truth,predictions)['tp'],oracle(0,set()))
