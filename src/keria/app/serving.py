import signal

from hio.base import doing
from keri import help

logger = help.ogler.getLogger()

class GracefulShutdownDoer(doing.Doer):
    """
    Shuts all Agency agents down before throwing a KeyboardInterrup to cause the Doist loop to exit,
    performing a graceful shutdown.
    Sets up signal handler in the Doer.enter lifecycle method.
    Checks for the shutdown flag being set in the Doer.recur lifecycle method.
    """
    def __init__(self, agency, **kwa):
        """
        Sets up the GracefulShutdownDoer with the Agency. Eventually the Agency should manage itself
        with its own exit function that shuts down all agents gracefully.

        Parameters:
            agency (Agency): The Agency containing Agent instances to be gracefully shut down
            kwa (dict): Additional keyword arguments for Doer initialization
        """
        self.agency = agency
        self.shutdown_received = False

        super().__init__(**kwa)

    def handle_sigterm(self, signum, frame):
        """Handler function for SIGTERM"""
        logger.info("Received SIGTERM, initiating graceful shutdown.")
        self.shutdown_received = True

    def handle_sigint(self, signum, frame):
        """Handler function for SIGINT"""
        logger.info("Received SIGINT, initiating graceful shutdown.")
        self.shutdown_received = True

    def shutdownAgency(self):
        """Helper function to shut down the agents."""
        logger.info("Stopping Agency")
        self.agency.shouldShutdown = True  # Set the shutdown flag in the Agency

    def enter(self, temp=False):
        """
        Sets up signal handlers.
        Lifecycle method called once when the Doist running this Doer enters the context for this Doer.
        """
        # Register signal handler
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        signal.signal(signal.SIGINT, self.handle_sigint)
        logger.info("Registered signal handlers for SIGTERM")

    def recur(self, tyme=None, tock=0.0, **opts):
        """Generator coroutine checking once per tock for shutdown flag"""
        # Checks once per tock if the shutdown flag has been set and if so initiates the shutdown process
        while not self.shutdown_received:
            yield tock # will iterate forever in here until shutdown flag set
        logger.info("Shutdown flag received, initiating graceful shutdown of agents")
        self.shutdownAgency()
        # Once shutdown_received is set, trigger agency shutdown which will eventually shut down
        # the Doist loop by throwing a KeyboardInterrupt
        return True # Returns a "done" status
