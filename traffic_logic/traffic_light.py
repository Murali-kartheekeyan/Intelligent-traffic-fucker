# traffic_logic/traffic_light.py
# This module contains the logic for controlling the traffic signal.

import time
from threading import Thread, Lock

class TrafficLightController:
    """
    Manages the state and timing of a single traffic light.
    The logic is now dynamic based on vehicle count.
    """
    def __init__(self):
        """
        Initializes the traffic light controller.
        """
        self.state = 'red'
        self.state_lock = Lock()
        
        # --- Dynamic Timing Attributes ---
        # Base duration for the green light in seconds
        self.green_light_base_duration = 5
        # Maximum duration for the green light to prevent excessive waiting
        self.green_light_max_duration = 20
        # Current calculated duration for the green light
        self.current_green_duration = self.green_light_base_duration
        self.duration_lock = Lock()

        print("TrafficLightController initialized. Initial state: RED")
        
        self.cycle_thread = Thread(target=self._run_dynamic_cycle, daemon=True)
        self.cycle_thread.start()

    def get_state(self):
        """
        Thread-safely gets the current state of the traffic light.
        """
        with self.state_lock:
            return {
                'red': self.state == 'red',
                'yellow': self.state == 'yellow',
                'green': self.state == 'green'
            }

    def _set_state(self, new_state):
        """
        Thread-safely sets the new state of the traffic light.
        """
        with self.state_lock:
            if self.state != new_state:
                self.state = new_state
                print(f"Traffic light state changed to: {self.state.upper()}")

    def update_logic_with_analysis(self, analysis_data):
        """
        Adjusts the green light duration based on real-time vehicle count.
        
        Args:
            analysis_data (dict): Data from the VideoAnalyzer, e.g., {'vehicle_count': 10}.
        """
        vehicle_count = analysis_data.get("vehicle_count", 0)
        
        # Simple dynamic logic: add 0.5 seconds per vehicle, up to a max.
        # This logic can be made more sophisticated.
        calculated_duration = self.green_light_base_duration + (vehicle_count * 0.5)
        
        # Thread-safely update the duration
        with self.duration_lock:
            # Clamp the duration between the base and max values
            self.current_green_duration = max(self.green_light_base_duration, 
                                              min(calculated_duration, self.green_light_max_duration))

    def _run_dynamic_cycle(self):
        """
        Runs a traffic light cycle where the green light duration is dynamic.
        """
        while True:
            # --- RED LIGHT STATE ---
            self._set_state('red')
            time.sleep(15)  # Fixed red light duration

            # --- GREEN LIGHT STATE ---
            self._set_state('green')
            with self.duration_lock:
                current_duration = self.current_green_duration
            print(f"Green light duration set to {current_duration:.1f} seconds.")
            time.sleep(current_duration)

            # --- YELLOW LIGHT STATE ---
            self._set_state('yellow')
            time.sleep(3)   # Fixed yellow light duration
