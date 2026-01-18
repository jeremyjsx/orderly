import asyncio
import logging

from app.events.payments.consumers import start_payment_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    asyncio.run(start_payment_consumer())
