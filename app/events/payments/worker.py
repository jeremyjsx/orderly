import asyncio

from app.core.logging import configure_logging
from app.events.payments.consumers import start_payment_consumer

configure_logging(json_logs=True, log_level="INFO")

if __name__ == "__main__":
    asyncio.run(start_payment_consumer())
