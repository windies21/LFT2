import os
import pytest
from asyncio import QueueEmpty
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.app.term import RotateTermFactory
from lft.consensus.layers.async_.async_layer import AsyncLayer
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator


async def setup_async_layers(voter_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    async_layers = []
    event_systems = []
    data_factories = []
    vote_factories = []
    for voter in voters:
        event_system = EventSystem()
        event_system.set_mediator(DelayedEventMediator)
        event_system.start(blocking=False)

        data_factory = DefaultDataFactory(voter)
        vote_factory = DefaultVoteFactory(voter)
        term_factor = RotateTermFactory(1)
        async_layer = AsyncLayer(SyncLayer(voter, event_system, data_factory, vote_factory, term_factor),
                                 voter,
                                 event_system,
                                 data_factory,
                                 vote_factory,
                                 term_factor)

        async_layers.append(async_layer)
        event_systems.append(event_system)
        data_factories.append(data_factory)
        vote_factories.append(vote_factory)

    return voters, event_systems, async_layers, data_factories, vote_factories


def get_event(event_system: EventSystem):
    _, _, event = event_system.simulator._event_tasks.get_nowait()
    return event


def verify_no_events(event_system):
    with pytest.raises(QueueEmpty):
        event = get_event(event_system)
        print("remain event: " + event)
