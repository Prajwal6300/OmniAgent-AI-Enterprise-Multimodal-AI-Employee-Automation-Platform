class OracleAdapter:
    async def fetch_purchase_order(self, po_number: str):
        return {"po_number": po_number, "vendor": "Global Tech", "total": 8500.00}
