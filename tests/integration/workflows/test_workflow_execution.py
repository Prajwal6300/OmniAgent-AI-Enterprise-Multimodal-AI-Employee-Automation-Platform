from automation.engine.engine import WorkflowEngine

def test_workflow_run_initialization():
    engine = WorkflowEngine()
    run = engine.init_run("run-1", "wf-1", {"invoice_id": "INV-100"})
    assert run.status == "PENDING"
    assert run.context["invoice_id"] == "INV-100"
