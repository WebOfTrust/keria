import signal

from hio.base import doing, Doist
from keri import help

logger = help.ogler.getLogger()

class GracefulShutdownDoer(doing.DoDoer):
    def __init__(self, doist, agency, **kwa):
        self.doist: Doist = doist
        self.agency = agency
        self.shutdown_flag = False

        # Register signal handler
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        signal.signal(signal.SIGINT, self.handle_sigterm)
        logger.info("Registered signal handlers for SIGTERM and SIGINT")

        super().__init__(doers=[self.shutdown], **kwa)

    def handle_sigterm(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown.")
        self.shutdown_flag = True

    def shutdown_agents(self, agents):
        logger.info("Stopping %s agents", len(agents))
        for caid in agents:
            self.agency.shut(self.agency.agents[caid])

    @doing.doize()
    def shutdown(self, tymth, tock=0.0):
        self.wind(tymth)
        while not self.shutdown_flag:
            yield tock

        # Once shutdown_flag is set, exit the Doist loop
        self.shutdown_agents(list(self.agency.agents.keys()))
        logger.info(f"Shutting down main Doist loop")
        self.doist.exit()