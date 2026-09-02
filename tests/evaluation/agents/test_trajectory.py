from agents.evaluation.evaluators.trajectory import TrajectoryEvaluator

def test_trajectory_evaluator():
    evaluator = TrajectoryEvaluator()
    score = evaluator.evaluate(["supervisor", "rag", "supervisor"], ["supervisor", "rag", "supervisor"])
    assert score == 1.0
