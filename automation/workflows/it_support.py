class ITSupportWorkflow:
    STEPS = [
        "parse_screenshot_error",
        "query_rag_runbooks",
        "create_jira_incident",
        "notify_oncall_engineer"
    ]
