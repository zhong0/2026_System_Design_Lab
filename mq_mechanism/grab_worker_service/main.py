from service.grabWorker import grabWorker
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

if __name__ == "__main__":
    logger.info("Grab worker starts.")
    worker = grabWorker()
    worker.run()
