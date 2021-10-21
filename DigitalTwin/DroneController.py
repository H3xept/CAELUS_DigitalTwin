from queue import Empty, Queue
import logging
import threading
from ProbeSystem.state_aggregator.state_aggregator import StateAggregator
from typing import Tuple, List
from .VehicleConnectionManager import VehicleConnectionManager
from .DroneCommander import DroneCommander
from .Interfaces.VehicleManager import VehicleManager
from .Interfaces.MissionManager import MissionManager
from .Interfaces.Stoppable import Stoppable
from .Probes.AnraTelemetryPush import AnraTelemetryPush

class DroneController(VehicleManager, MissionManager, Stoppable):
    def __init__(self):
        self.__connection_manager = VehicleConnectionManager(self)
        self.__commander = DroneCommander()
        self.__state_aggregator = StateAggregator('test_drone', should_manage_vehicle=False)
        self.__logger = logging.getLogger(__name__)
        self.__should_stop = False
        self.__mission_queue = Queue()
        self.__mission_poll_thread = None
        self.__state_aggregator_thread = None
        self.__executing_mission = False
        self.__setup_probes()
        self.__connection_manager.connect_to_vehicle()

    def __setup_probes(self):
        self.__logger.info('Setting up probes')
        anra_probe = AnraTelemetryPush('','','','')
        for stream_id in anra_probe.subscribes_to_streams():
            self.__state_aggregator.subscribe(stream_id, anra_probe)
        self.__state_aggregator.report_subscribers()
        
    def vehicle_available(self, vehicle):
        self.__logger.info(f'New vehicle available {vehicle}')
        self.__commander.set_vehicle(vehicle)
        
        self.__state_aggregator.set_vehicle(vehicle)
        self.__state_aggregator_thread = threading.Thread(target=self.__state_aggregator.idle, args=())
        self.__state_aggregator_thread.name = 'StateAggregator Main-Thread'
        self.__state_aggregator_thread.daemon = True
        self.__state_aggregator_thread.start()

        self.mission_poll_thread_start()
    
    def vehicle_timeout(self, vehicle):
        self.__logger.info(f'Vehicle timed out!')
        self.__should_stop = True
        self.__connection_manager.stop_connecting()
        self.__connection_manager.connect_to_vehicle()

    def poll_mission(self):
        while not self.__should_stop:
            if not self.__executing_mission:
                try:
                    waypoints_alt = self.__mission_queue.get(block=False)
                    self.__executing_mission = True
                    waypoints, alt = [[a[0], a[1]] for a in waypoints_alt], waypoints_alt[0][-1]

                    self.__logger.info('Received new mission')
                    self.__commander.set_mission(waypoints, altitude=alt)
                    self.__commander.start_mission()
                except Empty as e:
                    pass
                except Exception as e:
                    self.__logger.warn(e)
        self.__logger.info('Mission poll thread complete.')

    def mission_poll_thread_start(self):
        try:
            self.__logger.info('Mission poll thread start.')
            self.__mission_poll_thread = threading.Thread(target=self.poll_mission)
            self.__mission_poll_thread.name = 'Mission Poll'
            self.__mission_poll_thread.daemon = True
            self.__mission_poll_thread.start()
        except Exception as e:
            self.__logger.warn(e) 

    def add_mission(self, mission: Tuple[List[float], float]):
        self.__logger.info(f'Received new mission! Enqueueing...')
        self.__mission_queue.put(mission)

    def graceful_stop(self):
        self.__connection_manager.stop_connecting()
        self.__should_stop = True

    def halt(self):
        exit(-1)
