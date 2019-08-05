from typing import IO, Dict, Type
from lft.app.event import Gossiper
from lft.app.data import DefaultConsensusDataFactory, DefaultConsensusVoteFactory
from lft.app.event.logger import Logger
from lft.event import EventSystem, EventMediator
from lft.event.mediators import DelayedEventMediator
from lft.consensus.consensus import Consensus
from lft.consensus.data import ConsensusData, ConsensusVote
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent


class Node:
    def __init__(self, node_id: bytes):
        self.node_id = node_id
        self.event_system = EventSystem()
        self.event_system.set_mediator(DelayedEventMediator)

        self.received_data = set()
        self.received_votes = set()

        self._gossipers = {}
        self._logger = Logger(self.node_id, self.event_system.simulator)
        self._consensus = Consensus(
            self.event_system,
            self.node_id,
            DefaultConsensusDataFactory(self.node_id),
            DefaultConsensusVoteFactory(self.node_id))

    def __del__(self):
        self.close()

    def close(self):
        for gossiper in self._gossipers.values():
            gossiper.close()
        self._gossipers.clear()

        if self._consensus:
            self._consensus.close()
            self._consensus = None

        if self.event_system:
            self.event_system.close()
            self.event_system = None

    def start(self, blocking=True):
        self.event_system.start(blocking)

    def start_record(self, record_io: IO, mediator_ios: Dict[Type[EventMediator], IO]=None, blocking=True):
        self.event_system.start_record(record_io, mediator_ios, blocking)

    def start_replay(self, record_io: IO, mediator_ios: Dict[Type[EventMediator], IO]=None, blocking=True):
        self.event_system.start_replay(record_io, mediator_ios, blocking)

    def receive_data(self, data: ConsensusData):
        if data in self.received_data:
            print(f"{self.node_id} : receive data but ignored : {data}")
        else:
            print(f"{self.node_id} : receive data : {data}")
            self.received_data.add(data)

            event = ReceivedConsensusDataEvent(data)
            self.event_system.simulator.raise_event(event)

    def receive_vote(self, vote: ConsensusVote):
        if vote in self.received_votes:
            print(f"{self.node_id} : receive vote but ignored : {vote}")
        else:
            print(f"{self.node_id} : receive vote : {vote}")
            self.received_votes.add(vote)

            event = ReceivedConsensusVoteEvent(vote)
            self.event_system.simulator.raise_event(event)

    def register_peer(self, peer_id: bytes, peer: 'Node'):
        gossiper = Gossiper(self.event_system, self, peer)
        self._gossipers[peer_id] = gossiper

    def unregister_peer(self, peer_id: bytes):
        self._gossipers.pop(peer_id, None)
