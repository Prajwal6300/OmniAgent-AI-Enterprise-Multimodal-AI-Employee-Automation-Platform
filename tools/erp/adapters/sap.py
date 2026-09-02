class SAPAdapter:
    async def fetch_purchase_order(self, po_number: str):
        return {"po_number": po_number, "vendor": "ACME Corp", "total": 12500.00}
