# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""
import logging
import os
from base64 import b64decode
import json
import datetime
from dataclasses import asdict, dataclass, field
from typing import List
from urllib.parse import urlparse, urljoin
from types import MappingProxyType
from deprecation import deprecated

import falcon
import lmdb
from falcon import media
from hio.base import doing, Doer
from hio.core import http
from hio.help import decking

from keri import core, kering
from keri.app.notifying import Notifier
from keri.app.storing import Mailboxer

from keri.app import configing, keeping, habbing, storing, signaling, oobiing, agenting, \
    forwarding, querying, connecting, grouping
from keri.app.grouping import Counselor
from keri.app.keeping import Algos
from keri.core import coring, parsing, eventing, routing, serdering
from keri.core.coring import Ilks
from keri.core.signing import Salter
from keri.db.basing import OobiRecord
from keri.vc import protocoling

from keria.end import ending
from keri.help import helping, nowIso8601
from keri.peer import exchanging
from keri.vdr import verifying
from keri.vdr.credentialing import Regery
from keri.vdr.eventing import Tevery
from keri.app import challenging

from . import aiding, notifying, indirecting, credentialing, ipexing, delegating
from . import grouping as keriagrouping
from .serving import GracefulShutdownDoer
from .. import log_name, ogler, set_log_level
from ..core.httping import falconApp, createHttpServer
from ..peer import exchanging as keriaexchanging
from .specing import AgentSpecResource
from ..core import authing, longrunning, httping
from ..core.authing import Authenticater
from ..core.keeping import RemoteManager
from ..db import basing

logger = ogler.getLogger(log_name)

@dataclass
class KERIAServerConfig:
    """
    Provides a dataclass to define server config so it is easy to test with multiprocess.
    Dataclasses are Pickleable and can be passed to a new process.
    """
    # HTTP ports to use.
    # Admin port number the admin HTTP server listens on.
    # Default is 3901. KERIA_ADMIN_PORT also sets this
    adminPort: int = 3901
    # Local port number the HTTP server listens on.
    # Default is 3902. KERIA_HTTP_PORT also sets this
    httpPort: int | None = 3092
    # Boot port number the Boot HTTP server listens on.
    # WARNING: This port needs to be secured.
    # Default is 3903. KERIA_BOOT_PORT also sets this.
    bootPort: int = 3903

    # Agency master controller information and configuration
    # Name of controller. Default is 'keria'.
    name: str = "keria"
    # additional optional prefix to file location of KERI keystore
    base: str = ""
    # 21 character encryption passcode for keystore (is not saved)
    bran: str = None
    # configuration filename
    configFile: str = "keria"
    # directory override for configuration data
    configDir: str = None

    # TLS key material
    # TLS server private key file
    keyPath: str = None
    # TLS server signed certificate (public key) file
    certPath: str = None
    # TLS server CA certificate chain
    caFilePath: str = None

    # Logging configuration
    # Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL.
    # Default is CRITICAL
    logLevel: str = "CRITICAL"
    # path of the log file. If not defined, logs will not be written to the file.
    logFile: str = None

    # Agency configuration
    # Use CORS headers in the HTTP responses. Default is False
    cors: bool = True
    # Timeout for releasing agents. Default is 86400 seconds (24 hours)
    releaseTimeout: int = 86400
    # Controller Service Endpoint Location OOBI URLs to resolve at startup of each Agent. Makes a 'controller' EndRole and LocScheme in the database for each URL
    curls: List[str] = field(default_factory=list)
    # General Introduction OOBI URLs to resolve at startup of each Agent. For things like witnesses, watchers, mailboxes, and TEL observers.
    iurls: List[str] = field(default_factory=list)
    # Data OOBI URLs resolved at startup of each Agent. For things like ACDC schemas, ACDCs (credentials), or other CESR streams.
    durls: List[str] = field(default_factory=list)

    # Experimental configuration
    # Experimental password for boot endpoint. Enables HTTP Basic Authentication for the boot endpoint. Only meant to be used for testing purposes.
    bootPassword: str = None
    # Experimental username for boot endpoint. Enables HTTP Basic Authentication for the boot endpoint. Only meant to be used for testing purposes.
    bootUsername: str = None

def readConfigFile(configDir: str, configFile: str, temp=False):
    return configing.Configer(name=configFile,
                       base="",
                       headDirPath=configDir,
                       temp=temp,
                       reopen=True,
                       clear=False)

def runAgency(config: KERIAServerConfig, temp=False):
    """Runs a KERIA Agency with the given Doers by calling Doist.do(). Useful for testing."""
    set_log_level(config.logLevel, logger)
    if config.logFile is not None:
        ogler.headDirPath = config.logFile
        ogler.reopen(name="keria", temp=temp, clear=True)

    logger.info("Starting Agent for %s listening: admin/%s, http/%s, boot/%s",
                config.name, config.adminPort, config.httpPort, config.bootPort)
    logger.info("PID: %s", os.getpid())
    cf = readConfigFile(config.configDir, config.configFile, temp=temp) if config.configFile is not None else None
    agency = createAgency(config, temp=temp, cf=cf)
    doist = agencyDoist(setupDoers(agency, config))
    logger.info("The Agency is loaded and waiting for requests...")
    doist.do()

def agencyDoist(doers: List[Doer]):
    """Creates a Doist for the Agency doers and adds a graceful shutdown handler. Useful for testing."""
    tock = 0.03125
    doist = doing.Doist(limit=0.0, tock=tock, real=True)
    doers.append(GracefulShutdownDoer(agency=getAgency(doers)))
    doist.doers = doers
    return doist

def getAgency(doers):
    """Get the agency from a list of Doers. Used to get the Agency for the graceful agent shutdown."""
    for doer in doers:
        if isinstance(doer, Agency):
            return doer
    return None


class Agency(doing.DoDoer):
    """
    An Agency manages a collection of agents by using a set of subtasks to handle
    - agent provisioning
    - agent deletion
    - shutting down agents
    """

    def __init__(self, name, bran, base="", releaseTimeout=None,
                 configFile=None, configDir=None, adb=None, temp=False,
                 curls=None, iurls=None, durls=None, cf=None):
        """
        Initialize the Agency with the given parameters.

        Parameters:
            name (str): Name of the agency.
            bran (str | None): Passcode for the agency's keystore.
            base (str): Base directory for the agency's keystore.
            releaseTimeout (int | None): Timeout for releasing agents.
            configFile (str | None): Configuration file name for the agency.
            configDir (str | None): Directory for configuration files.
            adb (AgencyBaser | None): Optional AgencyBaser instance for database access.
            temp (bool): Whether to use a temporary database.
            curls (list | None): Controller Service Endpoint Location OOBI URLs to resolve at startup of each Agent.
            iurls (list | None): General Introduction OOBI URLs to resolve at startup of each Agent.
            durls (list | None): Data OOBI URLs resolved at startup of each Agent.
            cf (configing.Configer | None): Optional Configer instance for configuration data.
        """
        self.name = name
        self.base = base
        self.bran = bran
        self.temp = temp
        self.configFile = configFile
        self.shouldShutdown = False
        self.configDir = configDir
        self.cf = None
        self.curls = curls
        self.iurls = iurls
        self.durls = durls

        if cf is None and self.configFile is not None:
            self.cf = configing.Configer(name=self.configFile,
                                         base="",
                                         headDirPath=self.configDir,
                                         temp=temp,
                                         reopen=True,
                                         clear=False)
        else:
            self.cf = cf

        self.agents = dict()

        self.adb = adb if adb is not None else basing.AgencyBaser(name="TheAgency", base=base, reopen=True, temp=temp)
        super(Agency, self).__init__(doers=[Releaser(self, releaseTimeout=releaseTimeout)])

    def _load_config_for_agent(self, caid):
        """
        Loads configuration data for an agent by looking up the Agency's configuration and copying
        the agency config for the agent merged with curls, iurls, and durls specified by environment
        variables.

        Parameters:
            caid (str): The controller AID (Agent Identifier) for the agent.
        Returns:
            dict: A dictionary containing the agent's configuration data.
        """
        timestamp = nowIso8601()
        config = dict(self.cf.get() if self.cf is not None else { "dt": timestamp })

        # Renames sub-section of config
        habName = f"agent-{caid}"
        config_name = self.name if self.name else "keria"
        if config_name in config:
            config[habName] = config[config_name]
            del config[config_name]
        else:
            config[habName] = {}

        config[habName]["curls"] = config[habName].get("curls", [])
        config["iurls"] = config.get("iurls", [])
        config["durls"] = config.get("durls", [])
        if self.curls is not None and isinstance(self.curls, list):
            config[habName]["curls"] = config[habName]["curls"] + self.curls

        if self.iurls is not None and isinstance(self.iurls, list):
            config["iurls"] = config["iurls"] + self.iurls

        if self.durls is not None and isinstance(self.durls, list):
            config["durls"] = config["durls"] + self.durls
        return config

    def _write_agent_config(self, caid):
        """
        Writes the agent configuration as a modified copy of the agency configuration.

        Parameters:
            caid (str): The controller AID (Agent Identifier) for the agent.
        Returns:
            configing.Configer: A Configer instance containing the agent's configuration data.
        """
        config = self._load_config_for_agent(caid)
        cf = configing.Configer(name=f"{caid}",
                                base="",
                                human=False,
                                temp=self.temp,
                                reopen=True,
                                clear=False)
        cf.put(config)
        return cf

    def create(self, caid, salt=None):
        """
        Create and return a new agent with the given caid and optional salt.

        Returns:
            Agent: The newly created agent.

        Parameters:
            caid (str): The controller AID (Agent Identifier) for the new agent.
            salt (str): Optional QB64 salt for the agent's Habery. If not provided, a random salt will be used.
        """
        habName = f"agent-{caid}"
        ks = keeping.Keeper(name=caid,
                            base=self.base,
                            temp=self.temp,
                            reopen=True)
        agent_cf = self._write_agent_config(caid)
        # Create the Hab for the Agent with only 2 AIDs
        agentHby = habbing.Habery(name=caid, base=self.base, bran=self.bran, ks=ks, cf=agent_cf, temp=self.temp, salt=salt)
        agentHab = agentHby.makeHab(habName, ns="agent", transferable=True, delpre=caid)
        agentRgy = Regery(hby=agentHby, name=agentHab.name, base=self.base, temp=self.temp)

        agent = Agent(hby=agentHby,
                      rgy=agentRgy,
                      agentHab=agentHab,
                      caid=caid,
                      agency=self)

        self.adb.agnt.pin(keys=(caid,),
                          val=coring.Prefixer(qb64=agent.pre))

        self.adb.ctrl.pin(keys=(agent.pre,),
                          val=coring.Prefixer(qb64=caid))

        # add agent to cache
        self.agents[caid] = agent
        # start agents processes running
        self.extend([agent])

        return agent

    def delete(self, agent):
        """Deletes the agent from the agency and cleans up its resources."""
        self.adb.agnt.rem(key=agent.caid)
        # TODO call the agent's shutdown method to clean up resources instead of manually closing them below
        agent.hby.deleteHab(agent.caid)
        agent.hby.ks.close(clear=True)
        agent.hby.close(clear=True)

        del self.agents[agent.caid]

    @deprecated(deprecated_in="0.2.0-rc2", removed_in="1.0.0",
                details="Use Agency.shutdownagency and Agent.shutdownAgent instead.")
    def shut(self, agent):
        """
        Shuts down an agent and cleans up its resources.

        """
        logger.info(f"Shutting down agent {agent.caid}")
        agent.remove(agent.doers)
        self.remove([agent])
        del self.agents[agent.caid]
        try:
            agent.hby.ks.close(clear=False)
            agent.seeker.close(clear=False)
            agent.exnseeker.close(clear=False)
            agent.monitor.opr.close(clear=False)
            agent.notifier.noter.close(clear=False)
            agent.rep.mbx.close(clear=False)
            agent.registrar.rgy.close()
            agent.mgr.rb.close(clear=False)
            agent.hby.close(clear=False)
        except lmdb.Error as ex:  # Sometimes LMDB will throw an error if the DB is already closed
            logger.error(f"Error closing databases for agent {agent.caid}: {ex}")

    def get(self, caid):
        """
        Retrieve an agent from the agency's agent list by controller AID (caid).

        Returns:
            Agent: The agent associated with the given caid, or None if not found.
        """
        if caid in self.agents:
            agent = self.agents[caid]
            agent.last = helping.nowUTC()
            return agent

        aaid = self.adb.agnt.get(keys=(caid,))
        if aaid is None:
            return None

        ks = keeping.Keeper(name=caid,
                            base=self.base,
                            temp=self.temp,
                            reopen=True)

        agentHby = habbing.Habery(name=caid, base=self.base, bran=self.bran, ks=ks, temp=self.temp)

        agentHab = agentHby.habByName(f"agent-{caid}", ns="agent")
        if aaid.qb64 != agentHab.pre:
            raise kering.ConfigurationError(f"invalid agent aid={aaid.qb64}/{agentHab.pre} to controller aid={caid}")

        agentRgy = Regery(hby=agentHby, name=agentHab.name, base=self.base, temp=self.temp)
        agent = Agent(hby=agentHby, rgy=agentRgy, agentHab=agentHab, agency=self, caid=caid)

        self.agents[caid] = agent
        self.extend([agent])

        return agent

    def lookup(self, pre):
        """
        Look up an agent by either a managed AID prefix (pre) or its controller AID in the agency's database.

        Returns:
            Agent: The agent associated with the given prefix, or None if not found.
        """
        # Check to see if this is a managed AID
        if (prefixer := self.adb.aids.get(keys=(pre,))) is not None:
            caid = prefixer.qb64
        # Or if its an agent AID
        elif (prefixer := self.adb.ctrl.get(keys=(pre,))) is not None:
            caid = prefixer.qb64
        else:
            return None

        try:
            return self.get(caid)
        except kering.ConfigurationError:
            return None

    def incept(self, caid, pre):
        """Maps a given agent to its controller AID (caid) in the agency's database."""
        self.adb.aids.pin(keys=(pre,), val=coring.Prefixer(qb64=caid))

    def shutdownAgency(self):
        """Shuts down the agents in an agency in preparation for agency shutdown."""
        if len(self.agents) > 0:
            caids = list(self.agents.keys())
            for caid in caids:
                agent = self.agents[caid]
                if not agent.shouldShutdown:
                    agent.shouldShutdown = True
                if agent.done:
                    self.remove([agent])
                    del self.agents[caid]

    def recur(self, tyme=None, tock=0.0):
        """
        Checks once per loop to see if the Agency should shutdown.
        If so, it will shut down each agent and then exit the Agency by returning True for the task (DoDoer) completion status.
        """
        if self.shouldShutdown and len(self.agents) == 0:
            logger.info("Agency shutdown complete. Exiting Agency.")
            return True
        if self.shouldShutdown and len(self.agents) > 0:
            self.shutdownAgency()
        super(Agency, self).recur(tyme=tyme)
        return False # Task is not done, run forever until True is returned

    def exit(self, rdeeds=None, deeds=None):
        """
        Called once per agent since self.remove() calls self.exit() when cleaning up each agent.
        Should only trigger the Doist loop to exit once all agents have been removed.
        """
        super(Agency, self).exit(deeds=deeds if deeds else self.deeds)
        if len(self.agents) == 0 and self.shouldShutdown:
            raise KeyboardInterrupt("Agency shutdown complete. Exiting Agency.")

class Agent(doing.DoDoer):
    """
    An network accessible agent paired to a remote Signify controller holding keys at the edge.
    The top level, DoDoer task object representing the Habery (database) and all associated KEL,
    ACDC (TEL), and other processing for its Signify controller.

    This agent acts as a:
    - mailbox for communicating to and from the Signify controller and any AIDs it controls
    - delegation communication proxy for any AIDs the Signify controller controls
    - KEL host for each the Signify conroller, any AIDs it controlls, and the agent's KEL
    - TEL host for any registry or ACDC (credential) the Signify controller creates or manages
    - ACDC (credential) host for any ACDCs (credentials) the Signify controller creates or manages
    - Signify key index backup for the key index used by the Signify controller in the
      hierarchical deterministic key (HDK) management scheme used to select keys at the edge.
    """

    def __init__(self, hby, rgy, agentHab, agency, caid, **opts):
        """
        Initialize the Agent with the given Habery, Regery, and agent's Hab.
        Parameters:
            hby (Habery): The Habery instance for the agent's database access.
            rgy (Regery): The Regery instance for the agent's registry access.
            agentHab (Hab): The Hab instance representing the agent itself.
            agency (Agency): The Agency instance managing this agent.
            caid (str): The controller AID identifier for this agent.
            opts (dict): Additional options for the Agent initialization.

        Attributes:
            .agency (Agency): The Agency instance managing this agent.
            .caid (str): The Signify controller AID for this agent.
            .hby (Habery): The Habery instance for the agent's local database.
            .agentHab (Hab): The Hab instance representing the agent itself.
            .rgy (Regery): The Regery instance for the agent's registry access.
            .cfd (MappingProxyType): Configuration data for the agent.
            .tocks (MappingProxyType): Escrow timing configurations for the underlying Hio tasks comprising this agent.
            .last (datetime.datetime): Last activity timestamp for the agent.
            .shouldShutdown (bool): Flag indicating if the agent should shut down.
            .swain (delegating.Anchorer): Watches the delegator for delegation approval seals for inception and rotation.
            .counselor (Counselor): Handles multisig transaction signing orchestration including for multisig operations.
                in delegated identifiers.
            .org (connecting.Organizer): Contact data manager for all OOBI-based contacts for an agent.
            .mgr (RemoteManager): Manages local key index storage for remotely managed keys.
            .cues (Deck): Holds KEL and TEL event messages for processing.
            .groups (Deck): Holds multisig event messages for processing.
            .anchors (Deck): Holds delegation anchors for processing.
            .witners (Deck): Holds witness-related data for processing.
            .queries (Deck): Holds key state query messages for processing.
            .exchanges (Deck): Holds exchange messages for processing.
            .grants (Deck): Holds IPEX grant messages for processing.
            .admits (Deck): Holds IPEX admit messages for processing.
            .submits (Deck): Holds KEL messages to be resubmitted to witnesses to obtain receipts of.
            .witq (WitnessInquisitor): Retrieves key state from witnesses.
            .witPub (WitnessPublisher): Publishes key state to witnesses.
            .witDoer (WitnessReceiptor): Propagates key events and receipts across the current witness set.
            .witSubmitDoer (WitnessReceiptor): Resubmits KEL messages to witnesses to obtain receipts of.
            .rep (Respondant): Routes response 'exn' messages by topic and handles cues for receipt, reply, and replay messages.
            .notifier (Notifier): Notifies the agent of events and changes.
            .mux (Multiplexor): Coordinates peer-to-peer messages between group multisig participants.
            .verifier (Verifier): Verifies and escrows TEL events (registries, credentials).
            .registrar (Registrar): Creation and escrowing for registries and credential issuance and revocation.
            .credentialer (Credentialer): Handles the credential missing signature escrow and credential schema validation.
            .seeker (Seeker): Database indexing saved credentials to simplify searching.
            .exnseeker (ExnSeeker): Database indexing saved exchange 'exn' messages to simplify searching.
            .exc (Exchanger): Handles peer-to-peer message routing and processing.
            .submitter (Submitter): Submits the last event from a KEL to the witnesses to obtain receipts and propagate to all other witnesses.
            .monitor (Monitor): Monitors the agent's state and performs long-running tasks like credential issuance and revocation.
            .rvy (Revery): Reply event message processor for routing and processing 'rpy' messages.
            .kvy (Kevery): Key Event Log (KEL) event processor for routing and processing KEL messages.
            .tvy (Tevery): TEL event processor for routing and processing TEL messages.
            .parser (Parser): Parses incoming messages and routes them to the appropriate handlers.
            .doers (List[Doer]): List of Doers that handle various tasks for the agent.

         Subtasks (Doers, DoDoers):
            oobiery (Oobiery): Handles OOBI resolution.
            receiptor (Receiptor): Obtains receipts on key events from witnesses and propagates receipts to each current witness of a controller.
            witq (WitnessInquisitor): Retrieves key state from witnesses.
            witPub (WitnessPublisher): Publishes key state to witnesses.
            witDoer (WitnessReceiptor): Propagates key events and receipts across the current witness set.
            witSubmitDoer (WitnessReceiptor): Resubmits KEL messages to witnesses to obtain receipts of.
            rep (Respondant): Routes response 'exn' messages by topic and handles cues for receipt, reply, and replay messages.
            HaberyDoer: Handles setup and tear down for the Habery
            signaler (Signaler): Sends signals to the controller of the agent.
            notifier (Notifier): Notifies the agent of events and changes.
            submitter (Submitter): Submits the last event from a KEL to the witnesses to obtain receipts and propagate to all other witnesses.
            monitor (Monitor): Monitors the agent's state and performs long-running tasks like credential issuance and revocation.
            Initer: prints a log message when the agent is initialized with the agent and controller AIDs.
            Querier: Handles key state queries by sequence number, anchor, or prefix.
            Escrower: Handles all message escrows including KEL, TEL, Reply, and Exchange messages.
            Parser: Runs the Parser to parse incoming messages and route them to the appropriate handlers.
            Witnesser: Performs event receipting, catchup, and propagation all current witnesses for KEL events.
            Delegator: Handles delegated event processing.
            ExchangeSender: Sends exchange messages to other controllers.
            Granter: Handles IPEX grant messages.
            Admitter: Handles IPEX admit messages.
            GroupRequester: Watches for and handles multisig group requests by delegating to the Counselor.
            SeekerDoer: Handles database indexing and queries for saved credentials.
            ExnCueDoer: Handles database indexing and queries for saved exchange 'exn' messages.

        Data Buffers (Decks):
            cues (Deck): for KEL and TEL event messages.
            groups (Deck): multisig event messages.
            anchors (Deck): delegation anchors.
            witners (Deck): Holds witness-related data.
            queries (Deck): key state query messages.
            exchanges (Deck): exchange messages.
            grants (Deck): IPEX grant messages.
            admits (Deck): IPEX admit messages.
            submits (Deck): KEL messages to be resubmitted to witnesses to obtain receipts of.
        """
        self.agency = agency
        self.caid = caid
        self.hby = hby
        self.agentHab = agentHab
        self.rgy = rgy
        self.cfd = MappingProxyType(dict(self.hby.cf.get()) if self.hby.cf is not None else dict())
        self.tocks = MappingProxyType(self.cfd.get("tocks", {}))
        self.last = helping.nowUTC()
        self._shouldShutdown = False

        self.swain = delegating.Anchorer(hby=hby, proxy=agentHab)
        self.counselor = Counselor(hby=hby, swain=self.swain, proxy=agentHab)
        self.org = connecting.Organizer(hby=hby)

        oobiery = oobiing.Oobiery(hby=hby)

        self.mgr = RemoteManager(hby=hby)

        self.cues = decking.Deck()
        self.groups = decking.Deck()
        self.anchors = decking.Deck()
        self.witners = decking.Deck()
        self.queries = decking.Deck()
        self.exchanges = decking.Deck()
        self.grants = decking.Deck()
        self.admits = decking.Deck()
        self.submits = decking.Deck()

        receiptor = agenting.Receiptor(hby=hby)
        self.witq = agenting.WitnessInquisitor(hby=self.hby)
        self.witPub = agenting.WitnessPublisher(hby=self.hby)
        self.witDoer = agenting.WitnessReceiptor(hby=self.hby)
        self.witSubmitDoer = agenting.WitnessReceiptor(hby=self.hby, force=True)

        self.rep = storing.Respondant(hby=hby, cues=self.cues, mbx=Mailboxer(name=self.hby.name, temp=self.hby.temp))

        doers = [habbing.HaberyDoer(habery=hby), receiptor, self.witq, self.witPub, self.rep, self.swain,
                 self.counselor, self.witDoer, *oobiery.doers]

        signaler = signaling.Signaler()
        self.notifier = Notifier(hby=hby, signaler=signaler)
        self.mux = grouping.Multiplexor(hby=hby, notifier=self.notifier)

        # Initialize all the credential processors
        self.verifier = verifying.Verifier(hby=hby, reger=rgy.reger)
        self.registrar = credentialing.Registrar(agentHab=agentHab, hby=hby, rgy=rgy, counselor=self.counselor,
                                                 witPub=self.witPub, witDoer=self.witDoer, verifier=self.verifier)
        self.credentialer = credentialing.Credentialer(agentHab=agentHab, hby=self.hby, rgy=self.rgy,
                                                       registrar=self.registrar, verifier=self.verifier,
                                                       notifier=self.notifier)

        self.seeker = basing.Seeker(name=hby.name, db=hby.db, reger=self.rgy.reger, reopen=True, temp=self.hby.temp)
        self.exnseeker = basing.ExnSeeker(name=hby.name, db=hby.db, reopen=True, temp=self.hby.temp)

        challengeHandler = challenging.ChallengeHandler(db=hby.db, signaler=signaler)

        handlers = [challengeHandler]
        self.exc = exchanging.Exchanger(hby=hby, handlers=handlers)
        grouping.loadHandlers(exc=self.exc, mux=self.mux)
        protocoling.loadHandlers(hby=self.hby, exc=self.exc, notifier=self.notifier)
        self.submitter = Submitter(hby=hby, submits=self.submits, witRec=self.witSubmitDoer)
        self.monitor = longrunning.Monitor(hby=hby, swain=self.swain, counselor=self.counselor, temp=hby.temp,
                                           registrar=self.registrar, credentialer=self.credentialer, submitter=self.submitter, exchanger=self.exc)

        self.rvy = routing.Revery(db=hby.db, cues=self.cues)
        self.kvy = eventing.Kevery(db=hby.db,
                                   lax=True,
                                   local=False,
                                   rvy=self.rvy,
                                   cues=self.cues)
        self.kvy.registerReplyRoutes(router=self.rvy.rtr)

        self.tvy = Tevery(reger=self.verifier.reger,
                          db=hby.db,
                          local=False,
                          cues=self.cues)

        self.tvy.registerReplyRoutes(router=self.rvy.rtr)
        self.parser = parsing.Parser(framed=True,
                                     kvy=self.kvy,
                                     tvy=self.tvy,
                                     exc=self.exc,
                                     rvy=self.rvy,
                                     vry=self.verifier,
                                     local=True)  # disable misfit escrow until we can add another parser for remote.

        doers.extend([
            Initer(agentHab=agentHab, caid=caid, tock=self.tocks.get("initer", 0.0)),
            Querier(hby=hby, agentHab=agentHab, kvy=self.kvy, queries=self.queries,
                    tock=self.tocks.get("querier", 0.0)),
            Escrower(kvy=self.kvy, rgy=self.rgy, rvy=self.rvy, tvy=self.tvy, exc=self.exc, vry=self.verifier,
                     registrar=self.registrar, credentialer=self.credentialer, tock=self.tocks.get("escrower", 0.0)),
            ParserDoer(kvy=self.kvy, parser=self.parser, tock=self.tocks.get("parser", 0.0)),
            Witnesser(receiptor=receiptor, witners=self.witners, tock=self.tocks.get("witnesser", 0.0)),
            Delegator(agentHab=agentHab, swain=self.swain, anchors=self.anchors, tock=self.tocks.get("delegator", 0.0)),
            ExchangeSender(hby=hby, agentHab=agentHab, exc=self.exc, exchanges=self.exchanges,
                           tock=self.tocks.get("exchangeSender", 0.0)),
            Granter(hby=hby, rgy=rgy, agentHab=agentHab, exc=self.exc, grants=self.grants,
                    tock=self.tocks.get("granter", 0.0)),
            Admitter(hby=hby, witq=self.witq, psr=self.parser, agentHab=agentHab, exc=self.exc, admits=self.admits,
                     tock=self.tocks.get("admitter", 0.0)),
            GroupRequester(hby=hby, agentHab=agentHab, counselor=self.counselor, groups=self.groups,
                           tock=self.tocks.get("groupRequester", 0.0)),
            SeekerDoer(seeker=self.seeker, cues=self.verifier.cues, tock=self.tocks.get("seeker", 0.0)),
            ExchangeCueDoer(seeker=self.exnseeker, cues=self.exc.cues, queries=self.queries,
                            tock=self.tocks.get("exchangecue", 0.0)),
            self.submitter,
        ])

        super(Agent, self).__init__(doers=doers, **opts)

    @property
    def pre(self):
        return self.agentHab.pre

    @property
    def shouldShutdown(self):
        return self._shouldShutdown

    @shouldShutdown.setter
    def shouldShutdown(self, value):
        self._shouldShutdown = bool(value)

    def inceptSalty(self, pre, **kwargs):
        keeper = self.mgr.get(Algos.salty)
        keeper.incept(pre=pre, **kwargs)

        self.agency.incept(self.caid, pre)

    def inceptRandy(self, pre, verfers, digers, **kwargs):
        keeper = self.mgr.get(Algos.randy)
        keeper.incept(pre=pre, verfers=verfers, digers=digers, **kwargs)

        self.agency.incept(self.caid, pre)

    def inceptGroup(self, pre, mpre, verfers, digers):
        keeper = self.mgr.get(Algos.group)
        keeper.incept(pre=pre, mpre=mpre, verfers=verfers, digers=digers)

        self.agency.incept(self.caid, pre)

    def inceptExtern(self, pre, verfers, digers, **kwargs):
        keeper = self.mgr.get(Algos.extern)
        keeper.incept(pre=pre, verfers=verfers, digers=digers, **kwargs)

        self.agency.incept(self.caid, pre)

    def recur(self, tyme=None, tock=0.0):
        if self.shouldShutdown:
            self.shutdownAgent() # will call exit so no need to return
            return True # never gets here since shutdownAgent triggers exit
        super(Agent, self).recur(tyme=tyme)
        return False

    def shutdownAgent(self):
        self.remove(self.doers) # calls .exit()
        # Shut down all of the LMDBer subclasses to close open files.
        to_close = [self.seeker, self.exnseeker, self.monitor.opr,
                    self.notifier.noter, self.rep.mbx, self.registrar.rgy.reger, self.mgr.rb, self.hby]
        for db in to_close:
            try:
                db.close(clear=False)
                logger.debug(f"Closed database {db.__class__.__name__} for agent {self.caid}")
            except lmdb.Error as ex:  # Sometimes LMDB will throw an error if the DB is already closed
                logger.error(f"Error closing database {db.__class__.__name__} for agent {self.caid}: {ex}")
        logger.info(f"Agent {self.caid} shut down")

def createBootServerDoer(config: KERIAServerConfig, agency: Agency):
    """Create the Agent boot HTTP server and the Doer to run it. Returns only the Doer."""
    bootApp = falconApp()

    bootEnd = BootEnd(agency, username=config.bootUsername, password=config.bootPassword)
    bootApp.add_route("/boot", bootEnd)
    bootApp.add_route("/health", HealthEnd())

    bootServer = createHttpServer(config.bootPort, bootApp, config.keyPath, config.certPath, config.caFilePath)
    if not bootServer.reopen():
        raise RuntimeError(f"Cannot create boot HTTP server on port {config.bootPort}")
    return http.ServerDoer(server=bootServer)

def createAdminServerDoer(config: KERIAServerConfig, agency: Agency):
    """
    Create the Admin HTTP server and the Doer to run it.
    Returns the Doer and the Falcon app so the HTTP app can use it for OpenAPI docs.
    """
    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agency=agency)

    adminApp = falconApp()
    if config.cors:
        adminApp.add_middleware(middleware=httping.HandleCORS())
    adminApp.add_middleware(authing.SignatureValidationComponent(agency=agency, authn=authn, allowed=["/agent"]))
    adminApp.req_options.media_handlers.update(media.Handlers())
    adminApp.resp_options.media_handlers.update(media.Handlers())

    loadEnds(app=adminApp)
    aidEnd = aiding.loadEnds(app=adminApp, agency=agency, authn=authn)
    credentialing.loadEnds(app=adminApp, identifierResource=aidEnd)
    delegating.loadEnds(app=adminApp, identifierResource=aidEnd)
    notifying.loadEnds(app=adminApp)
    keriagrouping.loadEnds(app=adminApp)

    keriaexchanging.loadEnds(app=adminApp)
    ipexing.loadEnds(app=adminApp)

    adminServer = createHttpServer(config.adminPort, adminApp, config.keyPath, config.certPath, config.caFilePath)
    if not adminServer.reopen():
        raise RuntimeError(f"cannot create admin HTTP server on port {config.adminPort}")
    return adminApp, http.ServerDoer(server=adminServer)

def createHttpServerDoer(config: KERIAServerConfig, agency: Agency, adminApp: falcon.App):
    """Create the main HTTP server and the Doer to run it. Returns only the Doer."""
    happ = falconApp()
    happ.req_options.media_handlers.update(media.Handlers())
    happ.resp_options.media_handlers.update(media.Handlers())

    ending.loadEnds(agency=agency, app=happ)
    indirecting.loadEnds(agency=agency, app=happ)

    swagsink = http.serving.StaticSink(staticDirPath="./static")
    happ.add_sink(swagsink, prefix="/swaggerui")

    specEnd = AgentSpecResource(app=adminApp, title='KERIA Interactive Web Interface API')
    specEnd.addRoutes(happ)
    happ.add_route("/spec.yaml", specEnd)
    server = createHttpServer(config.httpPort, happ, config.keyPath, config.certPath, config.caFilePath)
    if not server.reopen():
        raise RuntimeError(f"cannot create local http server on port {config.httpPort}")
    return http.ServerDoer(server=server)

def createAgency(config: KERIAServerConfig, temp=False, cf=None):
    return Agency(
        name=config.name,
        base=config.base,
        bran=config.bran,
        configFile=config.configFile,
        configDir=config.configDir,
        releaseTimeout=config.releaseTimeout,
        curls=config.curls,
        iurls=config.iurls,
        durls=config.durls,
        temp=temp,
        cf=cf
    )

def setupDoers(agency: Agency, config: KERIAServerConfig, temp=False, cf=None):
    """
    Sets up the HIO coroutines the KERIA agent server is composed of including three HTTP servers for a KERIA agent server:
    1. Boot server for bootstrapping agents. Signify calls this with a signed inception event.
    2. Admin server for administrative tasks like creating agents.
    3. HTTP server for all other agent operations.

    Parameters:
        config (KERIAServerConfig): Configuration for the KERIA server.
        temp (bool): Whether to use a temporary database. Default is False. Useful for testing.
        cf (configing.Configer | None): Optional Configer instance for configuration data. Useful for testing.
    """
    bootServerDoer = createBootServerDoer(config, agency)
    adminApp, adminServerDoer = createAdminServerDoer(config, agency)

    doers = [agency, bootServerDoer, adminServerDoer]

    if config.httpPort:
        httpServerDoer = createHttpServerDoer(config, agency, adminApp)
        doers.append(httpServerDoer)
    return doers


class ParserDoer(doing.Doer):
    """ A Doer that continuously processes messages from the Parser."""

    def __init__(self, kvy, parser, tock=0.0):
        self.kvy = kvy
        self.parser = parser
        self.tock = tock
        super(ParserDoer, self).__init__(tock=self.tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        """
        Continually processes messages on the incoming message stream (ims).
        Inner parsator yields continually when the stream is empty, making this good for long-running
        servers.
        """
        if self.parser.ims:
            logger.info("Agent %s received:\n%s\n...\n", self.kvy, self.parser.ims[:1024])
        done = yield from self.parser.parsator()  # process messages continuously
        return done  # should never get here except forced close


class Witnesser(doing.Doer):
    """
    Uses the Receiptor to obtain key event receipts from witnesses or on rotation events to catch up
    witnesses as needed to the current key state.
    """

    def __init__(self, receiptor, witners, tock=0.0):
        self.receiptor = receiptor
        self.witners = witners
        self.tock = tock
        super(Witnesser, self).__init__(tock=self.tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        while True:
            if self.witners:
                msg = self.witners.popleft()
                serder = msg["serder"]

                # If we are a rotation event, may need to catch new witnesses up to current key state
                if serder.ked['t'] in (Ilks.rot, Ilks.drt):
                    adds = serder.ked["ba"]
                    for wit in adds:
                        yield from self.receiptor.catchup(serder.pre, wit)

                yield from self.receiptor.receipt(serder.pre, serder.sn)

            yield self.tock


class Delegator(doing.Doer):

    def __init__(self, agentHab, swain, anchors, tock=0.0):
        self.agentHab = agentHab
        self.swain = swain
        self.anchors = anchors
        self.tock = tock
        super(Delegator, self).__init__(tock=self.tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        if self.anchors:
            msg = self.anchors.popleft()
            sn = msg["sn"] if "sn" in msg else None
            self.swain.delegation(pre=msg["pre"], sn=sn, proxy=self.agentHab)

        return False


class ExchangeSender(doing.DoDoer):

    def __init__(self, hby, agentHab, exc, exchanges, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.exc = exc
        self.exchanges = exchanges
        self.tock = tock
        super(ExchangeSender, self).__init__(always=True, tock=self.tock)

    def recur(self, tyme, deeds=None):
        if self.exchanges:
            msg = self.exchanges.popleft()
            said = msg['said']
            if not self.exc.complete(said=said):
                self.exchanges.append(msg)
                return super(ExchangeSender, self).recur(tyme, deeds)

            serder, pathed = exchanging.cloneMessage(self.hby, said)

            pre = msg["pre"]
            rec = msg["rec"]
            topic = msg['topic']
            hab = self.hby.habs[pre]
            logger.debug("[%s | %s]: Current Message Body= %s", hab.name, hab.pre, msg)
            if self.exc.lead(hab, said=said):
                atc = exchanging.serializeMessage(self.hby, said)
                del atc[:serder.size]
                for recp in rec:
                    logger.debug("[%s | %s]: Sending on topic %s to recipient %s from %s", hab.name, hab.pre, topic, recp, pre)
                    postman = forwarding.StreamPoster(hby=self.hby, hab=self.agentHab, recp=recp, topic=topic)
                    try:
                        postman.send(serder=serder,
                                     attachment=atc)
                    except kering.ValidationError:
                        logger.info(f"unable to send to recipient={recp}")
                    else:
                        doer = doing.DoDoer(doers=postman.deliver())
                        self.extend([doer])

        return super(ExchangeSender, self).recur(tyme, deeds)


class Granter(doing.DoDoer):
    """
    Presents ACDC credentials to a recipient using the Grant action of the IPEX protocol
    by sending all relevant data including delegated KELs and chained ACDCs.
    """

    def __init__(self, hby, rgy, agentHab, exc, grants, tock=0.0):
        """
        Accepts a list of IPEX Grant cues to process.

        Parameters:
            hby (Habery): The Agent Habery.
            rgy (Regery): The Agent Regery.
            agentHab (Hab): The Agent Hab.
            exc (Exchanger): The Exchanger instance for this Agent.
            grants (decking.Deck): Queue of grant messages to process.
            tock (float): The time interval for processing grants.
        """
        self.hby = hby
        self.rgy = rgy
        self.agentHab = agentHab
        self.exc = exc
        self.grants: decking.Deck = grants
        self.tock = tock
        super(Granter, self).__init__(always=True, tock=self.tock)

    def _makeDoer(self, grant_msg: dict):
        return GrantDoer(
                hby=self.hby,
                rgy=self.rgy,
                agentHab=self.agentHab,
                exc=self.exc,
                granter=self,
                grants=self.grants,
                grant_msg=grant_msg,
                tock=self.tock)

    def postGrants(self):
        """
        Makes a GrantDoer per grant message to process the grant.
        """
        while self.grants:
            grant_msg = self.grants.popleft()
            self.extend([self._makeDoer(grant_msg)])

    def recur(self, tyme, deeds=None):
        """Doer lifecycle method to process grants. Continuously processes grants as they arrive."""
        self.postGrants()
        return super(Granter, self).recur(tyme, deeds)


class GrantDoer(doing.Doer):
    """
    GrantDoer is a Doer for a single IPEX Grant operation that runs the message transmission process
    for all KEL, TEL, and credential artifacts included in the Grant.

    This GrantDoer allows for KLI-like behavior where the .postGrant can use yield expressions to
    wait on the parent driver DoDoer to finish running the child StreamPoster DoDoer prior to
    cleaning itself up.
    """
    def __init__(self, hby, rgy, agentHab, exc, granter, grants, grant_msg, tock=0.0, **kwa):
        """
        Accepts a list of IPEX Grant cues to process.

        Parameters:
            hby (Habery): The Agent Habery.
            rgy (Regery): The Agent Regery.
            agentHab (Hab): The Agent Hab.
            exc (Exchanger): The Exchanger instance for this Agent.
            granter (Granter): The Granter instance to use for processing grants.
            grants (decking.Deck): Queue of grant messages to process.
            grant_msg
            tock (float): The time interval for processing grants.
        """
        if not grant_msg or not isinstance(grant_msg, dict):
            raise ValueError(f"Grant message missing or invalid: {grant_msg}")
        self.grant_msg = grant_msg
        self.hby = hby
        self.rgy = rgy
        self.agentHab = agentHab
        self.exc = exc
        self.parent = granter
        self.grants = grants
        self.tock = tock
        super(GrantDoer, self).__init__(tock=self.tock, **kwa)

    def gatherAgentKEL(self, pre, recp, postman):
        """Send the KEL of the agent to the recipient."""
        agent_evts = []
        for msg in self.agentHab.db.cloneDelegation(self.agentHab.kever):
            serder = serdering.SerderKERI(raw=msg)
            atc = msg[serder.size:]
            agent_evts.append((serder, atc))
        return agent_evts

    def getCredArtifacts(self, recp, credSaid):
        """Send to the recipient the ACDC and the KELs of the issuer, holder, and any delegators."""
        creder = self.rgy.reger.creds.get(keys=(credSaid,))
        cred_artifacts = ipexing.gatherArtifacts(self.hby, self.rgy.reger, creder, recp)
        chain_artifacts = self.getChainedArtifacts(recp, creder)
        return cred_artifacts + chain_artifacts

    def getChainedArtifacts(self, recp, creder):
        """
        Send to the recipient any chained ACDCs and the KELs of the issuers and holders of those
        ACDCS and the KELs of any of their delegators.
        """
        chain_artifacts = []
        sources = self.rgy.reger.sources(self.hby.db, creder)
        for source, atc in sources:
            chain_artifacts.extend(ipexing.gatherArtifacts(self.hby, self.rgy.reger, source, recp))
            chain_artifacts.append((source, atc))
        return chain_artifacts

    def postGrant(self):
        """
        Presents an ACDC by sending all relevant data and cryptographic artifacts in the following order:
        - the agent KEL artifacts, including any delegation chain artifats
        - the issuer KEL artifacts, including delegation artifacts
        - the holder KEL artifacts, including delegation artifacts
        - the ACDC registry artifacts
        - the ACDC credential itself
        This is repeated for any chained credentials except that the agent KEL is only sent once.
        """
        msg = self.grant_msg
        said = msg['said']
        if not self.exc.complete(said=said):
            self.grants.append(msg)
            return

        serder, pathed = exchanging.cloneMessage(self.hby, said)

        pre = msg["pre"]
        rec = msg["rec"]
        hab = self.hby.habs[pre]
        if self.exc.lead(hab, said=said):
            for recp in rec:
                postman = forwarding.StreamPoster(hby=self.hby, hab=self.agentHab, recp=recp, topic="credential")
                try:
                    agent_evts = self.gatherAgentKEL(pre, recp, postman)
                    credSaid = serder.ked['e']['acdc']['d']
                    cred_artifacts = self.getCredArtifacts(recp, credSaid)
                    artifacts = agent_evts + cred_artifacts
                    # Queue the artifacts for later sending by postman.deliver()
                    for serder, atc in artifacts:
                        postman.send(serder=serder, attachment=atc)
                except kering.ValidationError:
                    logger.info(f"unable to send to recipient={recp}")
                except KeyError:
                    logger.info(f"invalid grant message={serder.ked}")
                else:
                    doer = doing.DoDoer(doers=postman.deliver())
                    self.parent.extend([doer])
        return True

    def recur(self, tock=0.0, **opts):
        """Processes the IPEX Grant operation and then exits by returning True (done)."""
        self.postGrant()
        return True


class Admitter(doing.Doer):

    def __init__(self, hby, witq, psr, agentHab, exc, admits, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.witq = witq
        self.psr = psr
        self.exc = exc
        self.admits = admits
        self.tock = tock
        super(Admitter, self).__init__(tock=self.tock)

    def recur(self, tyme, tock=0.0, **opts):
        if self.admits:
            msg = self.admits.popleft()
            said = msg['said']
            if not self.exc.complete(said=said):
                self.admits.append(msg)
                return False

            admit, _ = exchanging.cloneMessage(self.hby, said)

            if 'p' not in admit.ked or not admit.ked['p']:
                print(f"Invalid admit message={admit.ked}, no grant listed")
                return False

            grant, pathed = exchanging.cloneMessage(self.hby, admit.ked['p'])

            embeds = grant.ked['e']
            acdc = embeds["acdc"]
            issr = acdc['i']

            # Lets get the latest KEL and Registry if needed
            self.witq.query(hab=self.agentHab, pre=issr)
            if "ri" in acdc:
                self.witq.telquery(hab=self.agentHab, pre=issr, ri=acdc["ri"], i=acdc["d"])

            for label in ("anc", "iss", "acdc"):
                ked = embeds[label]
                if label not in pathed or not pathed[label]:
                    print(f"missing path label {label}")
                    continue

                sadder = coring.Sadder(ked=ked)
                ims = bytearray(sadder.raw) + pathed[label]
                self.psr.parseOne(ims=ims)


class SeekerDoer(doing.Doer):

    def __init__(self, seeker, cues, tock=0.0):
        self.seeker = seeker
        self.cues = cues
        self.tock = tock
        super(SeekerDoer, self).__init__(tock=self.tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        if self.cues:
            cue = self.cues.popleft()
            if cue["kin"] == "saved":
                creder = cue["creder"]
                try:
                    self.seeker.index(said=creder.said)
                except Exception:
                    self.cues.append(cue)
                    return False
            else:
                self.cues.append(cue)
                return False


class ExchangeCueDoer(doing.Doer):

    def __init__(self, seeker, cues, queries, tock=0.0):
        self.seeker = seeker
        self.cues = cues
        self.queries = queries
        self.tock = tock
        super(ExchangeCueDoer, self).__init__(tock=self.tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        if self.cues:
            cue = self.cues.popleft()
            if cue["kin"] == "saved":
                said = cue["said"]
                try:
                    self.seeker.index(said=said)
                except Exception:
                    self.cues.append(cue)
                    return False
            elif cue["kin"] == "query":
                self.queries.append(cue['q'])
                return False
            else:
                self.cues.append(cue)
                return False


class Initer(doing.Doer):
    """Prints a message once an agent is initialized."""
    def __init__(self, agentHab, caid, tock=0.0):
        self.agentHab = agentHab
        self.caid = caid
        self.tock = tock
        super(Initer, self).__init__(tock=self.tock)

    def print_agent(self):
        """Prints agent and associated controller name and prefix """
        if not self.agentHab.inited:
            return False
        agent_label = f"  Agent Pre: {self.agentHab.pre}, Controller: {self.caid}"
        # if log level not info or lower just print
        if logger.level > logging.INFO:
            print(agent_label)
        else:
            logger.info(agent_label)
        return True

    def recur(self, tyme, tock=0.0, **opts):
        return self.print_agent()


class GroupRequester(doing.Doer):

    def __init__(self, hby, agentHab, counselor, groups, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.counselor = counselor
        self.groups = groups
        self.tock = tock
        super(GroupRequester, self).__init__(tock=self.tock)

    def recur(self, tyme, tock=0.0, **opts):
        """ Checks cue for group processing requests and handles any with Counselor """
        if self.groups:
            msg = self.groups.popleft()
            serder = msg["serder"]

            ghab = self.hby.habs[serder.pre]

            prefixer = coring.Prefixer(qb64=serder.pre)
            seqner = coring.Seqner(sn=serder.sn)
            saider = coring.Saider(qb64=serder.said)
            self.counselor.start(ghab=ghab, prefixer=prefixer, seqner=seqner, saider=saider)

        return False


class Querier(doing.DoDoer):
    """
    Performs key state queries depending on sequence number, anchor, or prefix.
    """

    def __init__(self, hby, agentHab, queries, kvy, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.queries = queries
        self.kvy = kvy
        self.tock = tock
        super(Querier, self).__init__(always=True, tock=self.tock)

    def recur(self, tyme, deeds=None):
        """ Processes query reqests submitting any on the cue"""
        if self.queries:
            msg = self.queries.popleft()
            if "pre" not in msg:
                return False

            pre = msg["pre"]

            if "sn" in msg:
                sn = int(msg['sn'], 16)
                seqNoDo = querying.SeqNoQuerier(hby=self.hby, hab=self.agentHab, pre=pre, sn=sn)
                self.extend([seqNoDo])
            elif "anchor" in msg:
                anchor = msg['anchor']
                anchorDo = querying.AnchorQuerier(hby=self.hby, hab=self.agentHab, pre=pre, anchor=anchor)
                self.extend([anchorDo])
            else:
                qryDo = querying.QueryDoer(hby=self.hby, hab=self.agentHab, pre=pre, kvy=self.kvy)
                self.extend([qryDo])

        return super(Querier, self).recur(tyme, deeds)


class Escrower(doing.Doer):
    def __init__(self, kvy, rgy, rvy, tvy, exc, vry, registrar, credentialer, tock=0.0):
        """ Recuring process or escrows for all components in an Agent

        Parameters:
            kvy (Kevery):
            rgy (Regery):
            rvy (Revery):
            tvy (Tevery):
            exc (Exchanger):
            vry (Verifier):
            registrar (Registrar): Credential TEL escrow processor
            credentialer (Credentialer): Credential escrow processor
        """
        self.kvy = kvy
        self.rgy = rgy
        self.rvy = rvy
        self.tvy = tvy
        self.exc = exc
        self.vry = vry
        self.registrar = registrar
        self.credentialer = credentialer
        self.tock = tock

        super(Escrower, self).__init__(tock=self.tock)

    def recur(self, tyme, tock=0.0, **opts):
        """ Process all escrows once per loop. """
        self.kvy.processEscrows()
        self.kvy.processEscrowDelegables()
        self.rgy.processEscrows()
        self.rvy.processEscrowReply()
        if self.tvy is not None:
            self.tvy.processEscrows()
        self.exc.processEscrow()
        self.vry.processEscrows()
        self.registrar.processEscrows()
        self.credentialer.processEscrows()
        return False
    
class Releaser(doing.Doer):
    def __init__(self, agency: Agency, releaseTimeout=86400):
        """ Check open agents and close if idle for more than releaseTimeout seconds
        Parameters:
            agency (Agency): KERIA agent manager
            releaseTimeout (int): Timeout in seconds
 
        """
        self.tock = 60.0
        self.agents = agency.agents
        self.agency = agency
        self.releaseTimeout = releaseTimeout

        super(Releaser, self).__init__(tock=self.tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        while True:
            idle = []
            for caid in self.agents:
                now = helping.nowUTC()
                if (now - self.agents[caid].last) > datetime.timedelta(seconds=self.releaseTimeout):
                    idle.append(caid)

            for caid in idle:
                self.agency.shut(self.agents[caid])
            yield self.tock

def loadEnds(app):
    opColEnd = longrunning.OperationCollectionEnd()
    app.add_route("/operations", opColEnd)
    opResEnd = longrunning.OperationResourceEnd()
    app.add_route("/operations/{name}", opResEnd)

    oobiColEnd = OOBICollectionEnd()
    app.add_route("/oobis", oobiColEnd)
    oobiResEnd = OobiResourceEnd()
    app.add_route("/oobis/{alias}", oobiResEnd)

    statesEnd = KeyStateCollectionEnd()
    app.add_route("/states", statesEnd)

    eventsEnd = KeyEventCollectionEnd()
    app.add_route("/events", eventsEnd)

    queryEnd = QueryCollectionEnd()
    app.add_route("/queries", queryEnd)

    configEnd = ConfigResourceEnd()
    app.add_route("/config", configEnd)


class BootEnd:
    """ Resource class for creating datastore in cloud ahab """

    def __init__(self, agency: Agency, username: str | None = None, password: str | None = None):
        """ Provides endpoints for initializing and unlocking an agent
        Parameters:
            agency (Agency): Agency for managing agents
            username (str): username for boot request
            password (str): password for boot request
        """
        self.username = username
        self.password = password
        self.agency = agency

    def parseBasicAuth(self, req: falcon.Request):
        schemePrefix = 'Basic '
        if req.auth is None or not req.auth.startswith(schemePrefix):
            return None, None

        token = b64decode(req.auth[len(schemePrefix):]).decode('utf-8')
        splitIndex = token.find(':')
        if splitIndex == -1:
            return None, None

        username = token[:splitIndex]
        password = token[splitIndex + 1:]

        return username, password


    def authenticate(self, req: falcon.Request):
        # Username AND Password is not set, so no need to authenticate
        if self.username is None and self.password is None:
            return

        if req.auth is None:
            raise falcon.HTTPUnauthorized(title="Unauthorized")

        try:
            username, password = self.parseBasicAuth(req)

            if username == self.username and password == self.password:
                return

        except Exception:
            raise falcon.HTTPUnauthorized(title="Unauthorized")

        raise falcon.HTTPUnauthorized(title="Unauthorized")

    def on_post(self, req: falcon.Request, rep: falcon.Response):
        """ Inception event POST endpoint

        Give me a new Agent.  Create Habery using ctrlPRE as database name, agentHab that anchors the caid and
        returns the KEL of agentHAB Stores ControllerPRE -> AgentPRE in database

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """

        self.authenticate(req)

        body = req.get_media()
        if "icp" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description='required field "icp" missing from body')
        icp = serdering.SerderKERI(sad=body["icp"])

        if "sig" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description='required field "sig" missing from body')
        siger = core.Siger(qb64=body["sig"])

        caid = icp.pre

        if self.agency.get(caid=caid) is not None:
            raise falcon.HTTPConflict(title="agent already exists",
                                      description=f"agent for controller {caid} already exists")

        agent = self.agency.create(caid=caid)

        try:
            ctrlHab = agent.hby.makeSignifyHab(name=agent.caid, ns="agent", serder=icp, sigers=[siger])
        except Exception:
            self.agency.delete(agent)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid icp event for caid {agent.caid}')

        if ctrlHab.pre != agent.caid:
            self.agency.delete(agent)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid icp event for caid {agent.caid}')

        # Client is requesting that the Agent track the Salty parameters
        if Algos.salty in body:
            salt = body[Algos.salty]
            stem = httping.getRequiredParam(salt, "stem")
            pidx = httping.getRequiredParam(salt, "pidx")
            tier = httping.getRequiredParam(salt, "tier")
            sxlt = httping.getRequiredParam(salt, "sxlt")
            icodes = httping.getRequiredParam(salt, "icodes")
            ncodes = httping.getRequiredParam(salt, "ncodes")

            mgr = agent.mgr.get(algo=Algos.salty)
            mgr.incept(agent.caid, icodes=icodes, ncodes=ncodes, sxlt=sxlt, pidx=pidx, kidx=0, stem=stem, tier=tier,
                       transferable=True)

        elif Algos.randy in body:
            rand = body[Algos.randy]
            if "pris" not in rand:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description='required field "pris" missing from body.rand')
            pris = rand["pris"]

            if "nxts" not in rand:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description='required field "nxts" missing from body.rand')
            nxts = rand["nxts"]

            mgr = agent.mgr.get(algo=Algos.randy)
            mgr.incept(agent.caid, verfers=ctrlHab.kever.verfers,
                       digers=ctrlHab.kever.digers,
                       prxs=pris, nxts=nxts)

        elif Algos.group in body:
            raise falcon.HTTPBadRequest(description="multisig groups not supported as agent controller")

        rep.status = falcon.HTTP_202
        rep.data = json.dumps(asdict(agent.agentHab.kever.state())).encode("utf-8")


class HealthEnd:
    """Health resource for determining that a container is live"""

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_OK
        resp.media = {"message": f"Health is okay. Time is {nowIso8601()}"}


class KeyStateCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary:  Display key event log (KEL) for given identifier prefix
        description:  If provided qb64 identifier prefix is in Kevers, return the current state of the
                      identifier along with the KEL and all associated signatures and receipts
        tags:
           - Key Event Log
        parameters:
          - in: path
            name: pre
            description: qb64 identifier prefix of KEL to load
            schema:
              type: string
            required: true
        responses:
           200:
              description: Key event log and key state of identifier
           404:
              description: Identifier not found in Key event database


        """
        agent = req.context.agent
        if "pre" not in req.params:
            raise falcon.HTTPBadRequest(description="required parameter 'pre' missing")

        pres = req.params.get("pre")
        pres = pres if isinstance(pres, list) else [pres]

        states = []
        for pre in pres:
            if pre not in agent.hby.kevers:
                continue

            kever = agent.hby.kevers[pre]
            states.append(asdict(kever.state()))

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(states).encode("utf-8")


class KeyEventCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary:  Display key event log (KEL) for given identifier prefix
        description:  If provided qb64 identifier prefix is in Kevers, return the current state of the
                      identifier along with the KEL and all associated signatures and receipts
        tags:
           - Key Event Log
        parameters:
          - in: path
            name: pre
            schema:
              type: string
            required: true
            description: qb64 identifier prefix of KEL to load
        responses:
           200:
              description: Key event log and key state of identifier
           404:
              description: Identifier not found in Key event database


        """
        agent = req.context.agent
        if "pre" not in req.params:
            raise falcon.HTTPBadRequest(description="required parameter 'pre' missing")

        pre = req.params.get("pre")
        preb = pre.encode("utf-8")
        events = []
        for _, fn, dig in agent.hby.db.getFelItemPreIter(preb, fn=0):
            if not (raw := agent.hby.db.cloneEvtMsg(pre=preb, fn=fn, dig=dig)):
                raise falcon.HTTPInternalServerError(f"Missing event for dig={dig}.")

            serder = serdering.SerderKERI(raw=bytes(raw))
            atc = raw[serder.size:]
            events.append(dict(ked=serder.ked, atc=atc.decode("utf-8")))

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(events).encode("utf-8")


class OOBICollectionEnd:

    def __init__(self):
        """ Create OOBI Collection endpoint instance
        """

    @staticmethod
    def on_post(req, rep):
        """ Resolve OOBI endpoint.

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Resolve OOBI and assign an alias for the remote identifier
        description: Resolve OOBI URL or `rpy` message by process results of request and assign 'alias' in contact
                     data for resolved identifier
        tags:
           - OOBIs
        requestBody:
            required: true
            content:
              application/json:
                schema:
                  description: OOBI
                  oneOf:
                    - type: object
                      properties:
                        oobialias:
                          type: string
                          description: alias to assign to the identifier resolved from this OOBI
                        url:
                          type: string
                          description:  URL OOBI
                        rpy:
                          type: object
                          description: unsigned KERI `rpy` event message with endpoints
        responses:
           202:
              description: OOBI resolution to key state successful

        """
        agent = req.context.agent
        body = req.get_media()

        if "url" in body:
            oobi = body["url"]
            dt = helping.nowUTC()

            obr = OobiRecord(date=helping.toIso8601(dt))
            if "oobialias" in body:
                obr.oobialias = body["oobialias"]

            agent.hby.db.oobis.pin(keys=(oobi,), val=obr)

        elif "rpy" in body:
            raise falcon.HTTPNotImplemented(description="'rpy' support not implemented yet")

        else:
            raise falcon.HTTPBadRequest(description="invalid OOBI request body, either 'rpy' or 'url' is required")

        oid = Salter().qb64
        op = agent.monitor.submit(oid, longrunning.OpTypes.oobi, metadata=dict(oobi=oobi))

        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")


class OobiResourceEnd:

    @staticmethod
    def on_get(req, rep, alias):
        """ OOBI GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            alias: option route parameter for specific identifier to get

        ---
        summary:  Get OOBI for specific identifier
        description:  Generate OOBI for the identifier of the specified alias and role
        tags:
           - OOBIs
        parameters:
          - in: path
            name: alias
            schema:
              type: string
            required: true
            description: human readable alias for the identifier generate OOBI for
          - in: query
            name: role
            schema:
              type: string
            required: true
            description: role for which to generate OOBI
        responses:
            200:
              description: An array of Identifier key state information
              content:
                  application/json:
                    schema:
                        description: Key state information for current identifiers
                        type: object
        """
        agent = req.context.agent
        hab = agent.hby.habByName(alias)
        if hab is None:
            raise falcon.HTTPBadRequest(description="Invalid alias to generate OOBI")

        role = req.params["role"]

        res = dict(role=role)
        if role in (kering.Roles.witness,):  # Fetch URL OOBIs for all witnesses
            oobis = []
            for wit in hab.kever.wits:
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http) or hab.fetchUrls(eid=wit,
                                                                                           scheme=kering.Schemes.https)
                if not urls:
                    raise falcon.HTTPNotFound(description=f"unable to query witness {wit}, no http endpoint")

                url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
                up = urlparse(url)
                oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/witness/{wit}"))
            res["oobis"] = oobis
        elif role in (kering.Roles.controller,):  # Fetch any controller URL OOBIs
            oobis = []
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http) or hab.fetchUrls(eid=hab.pre,
                                                                                           scheme=kering.Schemes.https)
            if not urls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
            up = urlparse(url)
            oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/controller"))
            res["oobis"] = oobis
        elif role in (kering.Roles.agent,):
            oobis = []
            roleUrls = hab.fetchRoleUrls(hab.pre, scheme=kering.Schemes.http,
                                         role=kering.Roles.agent) or hab.fetchRoleurls(hab.pre,
                                                                                       scheme=kering.Schemes.https,
                                                                                       role=kering.Roles.agent)
            if not roleUrls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            for eid, urls in roleUrls['agent'].items():
                url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
                up = urlparse(url)
                oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/agent/{eid}"))
                res["oobis"] = oobis
        else:
            rep.status = falcon.HTTP_404
            return

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")


class QueryCollectionEnd:

    @staticmethod
    def on_post(req, rep):
        """

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary:  Display key event log (KEL) for given identifier prefix
        description:  If provided qb64 identifier prefix is in Kevers, return the current state of the
                      identifier along with the KEL and all associated signatures and receipts
        tags:
          - Query
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                    - pre
                properties:
                  pre:
                    type: string
                    description: qb64 identifier prefix of KEL to load
                  anchor:
                    type: string
                    description: Anchor
                  sn:
                    type: string
                    description: Serial number
        responses:
           200:
              description: Key event log and key state of identifier
           404:
              description: Identifier not found in Key event database


        """
        agent = req.context.agent
        body = req.get_media()
        pre = httping.getRequiredParam(body, "pre")
        qry = dict(pre=pre)

        oid = pre
        if "anchor" in body:
            qry["anchor"] = body["anchor"]
            oid = f"{pre}.{body["anchor"]["d"]}"
        elif "sn" in body:
            qry["sn"] = body["sn"]
            oid = f"{pre}.{body["sn"]}"
        else:  # Must reset key state so we know when we have a new update.
            for (keys, saider) in agent.hby.db.knas.getItemIter(keys=(pre,)):
                agent.hby.db.knas.rem(keys)
                agent.hby.db.ksns.rem((saider.qb64,))
                agent.hby.db.ksns.rem((saider.qb64,))

        agent.queries.append(qry)
        op = agent.monitor.submit(oid, longrunning.OpTypes.query, metadata=qry)

        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")

class Submitter(doing.DoDoer):
    def __init__(self, hby, submits, witRec):
        """
        Process to re-submit the last event from the KEL to the witnesses for receipts and to propogate it to each witness
        """
        self.hby = hby
        self.submits = submits
        self.witRec = witRec

        super(Submitter, self).__init__(always=True)

    def recur(self, tyme, deeds=None):
        """Processes submit reqests submitting any on the cue"""
        if self.submits:
            msg = self.submits.popleft()
            alias = msg["alias"]
            hab = self.hby.habByName(name=alias)
            sn = hab.kever.sn
            if hab and hab.kever.wits:
                auths = {}
                if hasattr(msg, "code"):
                    code = msg["code"]
                    if code:
                        for wit in hab.kever.wits:
                            auths[wit] = f"{code}#{helping.nowIso8601()}"
                witDoer = self.witRec
                witDoer.force = True
                self.extend([witDoer])
                print("Re-submit waiting for witness receipts...")
                witDoer.msgs.append(dict(pre=hab.pre, sn=sn))

        else:
            for doer in self.doers:
                if doer.cues:
                    cue = doer.cues.popleft()

                    if len(doer.cues) == 0:
                        print("Re-submit received all witness receipts for", cue["pre"])
                        self.doers.remove(doer)

        return super(Submitter, self).recur(tyme, deeds)


class ConfigResourceEnd:

    @staticmethod
    def on_get(req, rep):
        """ Config GET endpoint

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary: Retrieve agent configuration
        description:  Retrieve agent configuration (only necessary fields are exposed)
        tags:
          - Config
        responses:
           200:
              description: Subset of configuration dict as JSON

        """
        agent = req.context.agent
        config = agent.hby.cf.get()
        subset = {key: config[key] for key in ["iurls"] if key in config}

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(subset).encode("utf-8")
