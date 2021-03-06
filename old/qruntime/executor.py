
import json
from hashlib import sha256
from twisted.application import service
from twisted.python import log
from .urbject import create_power_for_memid, Urbject
from .pack import list_authorities
from .turn import Turn
from .memory import create_memory
from . import util

class ExecutionServer(service.Service):
    def __init__(self, db, vatid, comms):
        self.db = db
        self.vatid = vatid
        self._comms_server = comms
        self._debug_processed_counter = 0

    def process_request(self, msg, from_vatid):
        # main request-execution handler
        log.msg("PROCESS %s" % (msg,))
        try:
            self._process_request(msg, from_vatid)
        except:
            # TODO: think through exception handling
            raise
        self._debug_processed_counter += 1

    def _process_request(self, msg, from_vatid):
        # really, you should ignore from_vatid
        command = str(msg["command"])
        if command == "execute":
            memid = str(msg["memid"])
            powid = create_power_for_memid(self.db, memid)
            t = Turn(self, self.db)
            t.start_turn(msg["code"], powid, msg["args_json"], from_vatid)
            return
        if command == "invoke":
            urbjid = str(msg["urbjid"])
            u = Urbject(self.db, urbjid)
            code, powid = u.get_code_and_powid()
            t = Turn(self, self.db)
            t.start_turn(code, powid, msg["args_json"], from_vatid)
            return
        #raise ValueError("unknown command '%s'" % command)
        log.msg("ignored command '%s'" % command)

    def send_message(self, target_vatid, msg):
        self._comms_server.send_message(target_vatid, msg)

    # debug / CLI tools, triggered by 'poke'

    def send_execute(self, vatid, memid, code, args):
        msg = {"command": "execute",
               "memid": memid,
               "code": code,
               "args_json": json.dumps(args)}
        self._comms_server.send_message(vatid, json.dumps(msg))

    def send_invoke(self, vatid, urbjid, args):
        msg = {"command": "invoke",
               "urbjid": urbjid,
               "args_json": json.dumps(args)}
        self._comms_server.send_message(vatid, json.dumps(msg))

    def poke(self, body):
        if body.startswith("send "):
            send_msg = json.loads(body[len("send "):])
            vatid, urbjid = util.parse_spid(send_msg["spid"])
            msg = {"command": "invoke",
                   "urbjid": urbjid,
                   "args_json": send_msg["args"]}
            self._comms_server.send_message(vatid, json.dumps(msg))
            return "message sent"
        if body.startswith("create-memory"):
            memid = create_memory(self.db)
            return "created memory %s" % memid
        if body.startswith("execute "):
            cmd, vatid, memid = body.strip().split()
            code = ("def call(args, power):\n"
                    "    log('I have power!')\n")
            args = {"foo": 12}
            self.send_execute(vatid, memid, code, args)
            return "execute sent"
        if body.startswith("invoke "):
            cmd, vatid, urbjid = body.strip().split()
            args = {"foo": 12}
            self.send_invoke(vatid, urbjid, args)
            return "invoke sent"
        self._comms_server.trigger_inbound()
        self._comms_server.trigger_outbound()
        return "I am poked"

    def get_object_graph(self):
        # all potential objects are in the database, so we just pull the
        # whole thing into RAM and give it to the frontend to render as they
        # please. The resulting 'graph' object will look like:
        #
        #  URBJID: {type: "urbject", powid: POWID, codeid: SHA256(code)}
        #  POWID:  {type: "power", powers: [POWERS..]}
        #  MEMID:  {type: "memory", powers: [POWERS..]}
        #
        # where each element of POWERS is one of:
        #
        #  POWER: {type: "native", swissnum: "make_urbject"/..}
        #  POWER: {type: "reference", swissnum: SPID}
        #  POWER: {type: "memory", swissnum: MEMID}
        #
        c = self.db.cursor()
        graph = {}
        c.execute("SELECT `urbjid`,`powid`,`code` FROM `urbjects`")
        for (urbjid,powid,code) in c.fetchall():
            graph[urbjid] = {"type": "urbject",
                             "powid": powid,
                             "codeid": sha256(code).hexdigest()}
        c.execute("SELECT `powid`,`power_json` FROM `power`")
        for (powid,power_json) in c.fetchall():
            powers = []
            for (power_type, swissnum) in list_authorities(power_json, False):
                if power_type == "reference":
                    vatid, urbjid = swissnum
                    swissnum = util.make_spid(vatid, urbjid)
                powers.append({"type": power_type,
                               "swissnum": swissnum})
            graph[powid] = {"type": "power",
                            "powers": powers}
        c.execute("SELECT `memid`,`data_json` FROM `memory`")
        for (memid,data_json) in c.fetchall():
            powers = []
            for (power_type, swissnum) in list_authorities(data_json, False):
                if power_type == "reference":
                    vatid, urbjid = swissnum
                    swissnum = util.make_spid(vatid, urbjid)
                powers.append({"type": power_type,
                               "swissnum": swissnum})
            graph[memid] = {"type": "memory",
                            "powers": powers}
        return graph
