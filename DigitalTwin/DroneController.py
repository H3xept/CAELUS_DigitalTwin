from queue import Empty, Queue
import logging
import threading
from ProbeSystem.state_aggregator.state_aggregator import StateAggregator
from typing import Tuple, List
from dataclasses import dataclass
import os,signal
import time

from .MissionWriter import MissionWriter
from DigitalTwin.Interfaces.TimeSeriesHandler import TimeSeriesHandler
from DigitalTwin.Probes.ThermalModelProbe import ThermalModelProbe
from .VehicleConnectionManager import VehicleConnectionManager
from .DroneCommander import DroneCommander
from .Interfaces.VehicleManager import VehicleManager
from .Interfaces.MissionManager import MissionManager
from .Interfaces.Stoppable import Stoppable
from .Probes.AnraTelemetryPush import AnraTelemetryPush
from .Probes.Aeroacoustic import Aeroacoustic
from .Probes.TelemetryDisplay import TelemetryDisplay
from .Probes.QuadrotorBatteryDischarge import QuadrotorBatteryDischarge
from .Interfaces.TimeSeriesHandler import TimeSeriesHandler
from .PayloadModels import ControllerPayload
from .TelemetryFeedback import TelemetryFeedback

@dataclass
class Mission():
    waypoints: List[Tuple[float, float, float]]
    operation_id: str
    control_area_id: str
    reference_number: str
    drone_registration_number: str
    drone_id: str
    dis_token: str

class DroneController(VehicleManager, MissionManager, Stoppable):
    def __init__(self, controller_payload: ControllerPayload):
        self.__controller_payload = controller_payload
        self.__connection_manager = VehicleConnectionManager(self)
        self.__commander = DroneCommander()
        self.__state_aggregator = StateAggregator(controller_payload.drone_id if controller_payload is not None else "unknown_id", should_manage_vehicle=False)
        self.__logger = logging.getLogger(__name__)
        self.__state_aggregator_thread = None
        self.__mission_writer = MissionWriter(controller_payload.operation_id)
        self.__setup_probes()
        self.__connection_manager.connect_to_vehicle()
        self.__telemetry_feedback = TelemetryFeedback()

    def __setup_probes(self):
        self.__logger.info('Setting up probes')
        self.__anra_probe = AnraTelemetryPush()
        
        self.__battery_discharge_probe = QuadrotorBatteryDischarge()
        # TEMPORARY -- THIS SHOULD GO IN THE SIMULATOR
        self.__thermal_model_probe = ThermalModelProbe(integrate_every_us= 0.004 / 3600 )
        
        # Coupled but only instance that requires cross probe communication
        # THIS MUST NOT BE DELETED
        self.__anra_probe.set_payload_handler(self.__thermal_model_probe)
        # ----

        self.__aeroacoustic_probe = Aeroacoustic()

        for probe in [
            self.__anra_probe,
            self.__battery_discharge_probe,
            self.__thermal_model_probe,
            self.__aeroacoustic_probe
        ]:
            for stream_id in probe.subscribes_to_streams():
                self.__state_aggregator.subscribe(stream_id, probe)
        self.__state_aggregator.report_subscribers()
    
    # Called by vehicle when the mission has been completed
    def mission_complete(self):
        print("Mission complete. Waiting 2 seconds to allow other threads to sync.")
        time.sleep(2)
        self.__logger.info('Writing mission log file...')
        self.__mission_writer.save()
        self.__logger.info('Writing aeroacoustic input file (OST) ...')
        self.__aeroacoustic_probe.save()
        os.kill(os.getpid(), signal.SIGINT)

    def vehicle_available(self, vehicle):
        
        vehicle.set_controller(self)

        self.__logger.info(f'New vehicle available {vehicle}')
        self.__commander.set_vehicle(vehicle)
        
        self.__state_aggregator.set_vehicle(vehicle)
        self.__state_aggregator_thread = threading.Thread(target=self.__state_aggregator.idle, args=())
        self.__state_aggregator_thread.name = 'StateAggregator Main-Thread'
        self.__state_aggregator_thread.daemon = True
        self.__state_aggregator_thread.start()

        self.__battery_discharge_probe.set_vehicle(vehicle)
        
        self.__load_mission_from_payload()

    def __load_mission_from_payload(self):
        if self.__controller_payload is not None:
            self.__logger.info(f'Loading mission from configuration payload')
            self.add_mission(Mission(
                self.__controller_payload.waypoints,
                self.__controller_payload.operation_id,
                self.__controller_payload.control_area_id,
                self.__controller_payload.operation_reference_number,
                self.__controller_payload.drone_registration_number,
                self.__controller_payload.drone_id,
                self.__controller_payload.dis_auth_token
            ))

            self.__mission_writer.set_battery(self.__battery_discharge_probe.get_battery())
            self.__mission_writer.set_thermal_model(self.__thermal_model_probe)
            self.__mission_writer.start()

            self.__telemetry_feedback.set_battery(self.__battery_discharge_probe.get_battery())
            self.__telemetry_feedback.set_thermal_model(self.__thermal_model_probe)
            self.__telemetry_feedback.start()

    def vehicle_timeout(self, vehicle):
        self.__logger.info(f'Vehicle timed out!')
        self.__connection_manager.stop_connecting()
        self.__connection_manager.connect_to_vehicle()

    def add_mission(self, mission: Mission):
        self.__logger.info(f'Received new mission!')
        try:
            waypoints_alt = mission.waypoints
        
            self.__commander.set_mission(waypoints_alt)
            self.__commander.start_mission()
            self.__anra_probe.start_sending_telemetry(
                drone_registration=mission.drone_registration_number,
                operation_id=mission.operation_id,
                control_area_id=mission.control_area_id,
                reference_number=mission.reference_number,
                dis_token=mission.dis_token
            )

        except Empty as e:
            pass
        except Exception as e:
            self.__logger.warn(e)

    def graceful_stop(self):
        self.__connection_manager.stop_connecting()

    def halt(self):
        exit(-1)

    def set_time_series_handler(self, ts_handler: TimeSeriesHandler):
        assert ts_handler is not None
        self.__telemetry_feedback.set_time_series_handler(ts_handler)