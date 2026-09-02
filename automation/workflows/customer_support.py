class CustomerSupportWorkflow:
    STEPS = [
        "transcribe_support_call",
        "extract_sentiment_and_issue",
        "fetch_customer_crm_record",
        "draft_agent_response"
    ]
