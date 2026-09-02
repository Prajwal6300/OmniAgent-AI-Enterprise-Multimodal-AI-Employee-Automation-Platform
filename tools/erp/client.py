class ERPClient:
    def __init__(self, adapter):
        self.adapter = adapter

    async def get_po(self, po_number: str):
        return await self.adapter.fetch_purchase_order(po_number)
