from mq_tool.rabbitmqPublisher import rabbitmqPublisher


class raiseGrabSvc:
    def __init__(self):
        self.publisher = rabbitmqPublisher()

    async def enqueue(self, payload: dict) -> bool:
        return await self.publisher.publish(payload)

    async def control(self, payload: dict, queue: str) -> bool:
        return await self.publisher.publish(payload, queue=queue)
