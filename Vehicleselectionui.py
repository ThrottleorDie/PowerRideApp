from optparse import Values
import random
import json
import os
import webbrowser
import folium
import geocoder
import matplotlib.pyplot as plt
import os

from datetime import datetime

from kivy.app import App
from plyer import accelerometer
from time import time
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.video import Video
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image  # For displaying static images
from kivy.core.image import Image as CoreImage  # For loading from memory
import matplotlib.pyplot as plt
import io


def get_fake_heart_rate():
    return random.randint(65, 140)

class IntroScreen(Screen):
    def on_enter(self):
        video_path = os.path.join(os.getcwd(), 'ThrottleorDieVideo.mp4')
        video = Video(source=video_path, state='play', options={'eos': 'stop'})
        video.bind(on_eos=self.on_video_end)
        self.add_widget(video)
        video.size = self.size
        video.pos = self.pos

        # Fallback in case eos doesn't trigger
        Clock.schedule_once(self.switch_to_map, 6)

    def on_video_end(self, *args):
        self.manager.current = 'map'

    def switch_to_map(self, *args):
        self.manager.current = 'map'

class BubbleButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = 44
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.9, 1)  # iOS-style blue
        self.color = (1, 1, 1, 1)  # white text
        self.font_size = 16
        self.padding = (10, 10)
        self.radius = [20]  # rounded corners

        with self.canvas.before:
            Color(*self.background_color)
            self.rect = RoundedRectangle(radius=self.radius)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
   

class VehicleSelector(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.ride_location = None
        self.current_heart_rate = None
        self.heart_rate_zone = None
        self.heart_rate_log = []

        # Map style selector
        self.map_style_spinner = Spinner(
            text='Select Map Style',
            values=['OpenStreetMap', 'Stamen Terrain'],
            size_hint=(1, None),
            height=44
        )
        self.add_widget(self.map_style_spinner)

        # Vehicle buttons
        for vehicle in ['ATC', 'ATV','UTV', 'E-Bike', 'Dirt Bike', 'Snowmobile']:
            btn = BubbleButton(text=vehicle)
            btn.bind(on_press=self.select_vehicle)
        self.add_widget(btn)

        # Terrain selector with Gravel added
        self.terrain_spinner = Spinner(
            text='Select Terrain',
            values=['Trail', 'Sand', 'Snow', 'Mud', 'Rocks'],
            size_hint=(1, None),
            height=44
        )
        self.add_widget(self.terrain_spinner)

    def select_vehicle(self, instance):
        selected = instance.text
        print(f"Vehicle selected: {selected}")
        # You can store this in a log or sync it with ride metadata

# 🔥 Jump Mode Buttons
        self.jump_start_btn = Button(text="Start Jump", size_hint=(1, 0.2))
        self.jump_start_btn.bind(on_press=self.start_jump_tracking)
        self.add_widget(self.jump_start_btn)

        self.jump_stop_btn = Button(text="Stop Jump", size_hint=(1, 0.2))
        self.jump_stop_btn.bind(on_press=self.stop_jump_tracking)
        self.add_widget(self.jump_stop_btn)

        self.view_jumps_btn = Button(text="View Top Jumps", size_hint=(1, 0.2))
        self.view_jumps_btn.bind(on_press=self.view_top_jumps)
        self.add_widget(self.view_jumps_btn)

        self.graph_btn = Button(text="Graph Force vs Heart Rate", size_hint=(1, 0.2))
        self.graph_btn.bind(on_press=self.graph_jump_force_vs_heart_rate)
        self.add_widget(self.graph_btn)
        self.jump_history_btn = Button(text="View Jump History", size_hint=(1, 0.2))
        self.jump_history_btn.bind(on_press=self.view_jump_history)
        self.add_widget(self.jump_history_btn)
        self.view_jumps_btn = Button(text="View Top Jumps", size_hint=(1, 0.2))
        self.view_jumps_btn.bind(on_press=self.view_top_jumps)
        self.add_widget(self.view_jumps_btn)

# 🧗 Hill Climb Mode Buttons
        self.hill_climb_btn = Button(text="Hill Climb Mode", size_hint=(1, None), height=50)
        self.hill_climb_btn.bind(on_press=self.toggle_hill_climb_mode)
        self.layout.add_widget(self.hill_climb_btn)

        self.view_climbs_btn = Button(text="View Climb History", size_hint=(1, None), height=50)
        self.view_climbs_btn.bind(on_press=self.view_climb_history)
        self.layout.add_widget(self.view_climbs_btn)

        self.top_climbs_btn = Button(text="Top Climbs", size_hint=(1, None), height=50)
        self.top_climbs_btn.bind(on_press=self.view_top_climbs)
        self.layout.add_widget(self.top_climbs_btn)
        self.climb_heart_rates = []


    def start_jump_tracking(self):
        self.jump_data = []
        self.jump_start_time = time()
        accelerometer.enable()
        Clock.schedule_interval(self.record_acceleration, 0.05)
        print("Jump tracking started.")

    def record_acceleration(self, dt):
        acc = accelerometer.acceleration
        if acc:
            self.jump_data.append((time(), acc))

    def stop_jump_tracking(self):
        Clock.unschedule(self.record_acceleration)
        accelerometer.disable()
        self.jump_end_time = time()
        print("Jump tracking stopped.")
        self.analyze_jump()

    def analyze_jump(self):
        airtime = self.jump_end_time - self.jump_start_time
        height = 0.5 * 9.81 * (airtime / 2) ** 2

        start_coords = self.ride_location
        end_coords = self.get_current_gps()  # You’ll need to implement this
        length = self.calculate_distance(start_coords, end_coords)

        peak_acc = max(abs(acc[1][2]) for acc in self.jump_data)  # Z-axis
        mass = self.user_mass + self.vehicle_mass  # Let user input these
        force = mass * peak_acc

        jump_record = {
            "height": round(height, 2),
            "length": round(length, 2),
            "force": round(force, 2),
            "terrain": self.terrain_spinner.text,
            "heart_rate_bpm": self.current_heart_rate,
            "timestamp": time()
    }

        self.save_jump(jump_record)
        print(f"Jump recorded: {jump_record}")

    def save_jump(self, jump_record):
        log_file = "jump_log.json"
        jumps = []
        if os.path.exists(log_file):
           with open(log_file, "r") as f:
            jumps = json.load(f)
        jumps.append(jump_record)
        with open(log_file, "w") as f:
            json.dump(jumps, f, indent=4)
    def view_top_jumps(self, instance=None):
        try:
            with open("jump_log.json", "r") as f:
                jumps = json.load(f)
            top_jumps = sorted(jumps, key=lambda j: j['height'], reverse=True)[:5]
            content = "\n".join([
                f"{i+1}. Height: {j['height']}m | Length: {j['length']}m | Force: {j['force']}N | Terrain: {j['terrain']}"
                for i, j in enumerate(top_jumps)
        ])
        except Exception as e:
            content = f"Error loading jumps: {e}"

        popup = Popup(title="Top 5 Jumps", content=Label(text=content), size_hint=(0.8, 0.6))
        popup.open()

    def graph_jump_force_vs_heart_rate(self, instance=None):
        try:
            with open("jump_log.json", "r") as f:
                jumps = json.load(f)

            forces = [j['force'] for j in jumps if 'force' in j]
            heart_rates = [j['heart_rate'] for j in jumps if 'heart_rate' in j]

            if not forces or not heart_rates:
                raise ValueError("Missing force or heart rate data.")

            fig, ax = plt.subplots()
            ax.plot(heart_rates, forces, marker='o')
            ax.set_xlabel("Heart Rate (BPM)")
            ax.set_ylabel("Jump Force (N)")
            ax.set_title("Jump Force vs Heart Rate")

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            im = CoreImage(buf, ext='png')

            popup = Popup(title="Force vs Heart Rate", content=Image(texture=im.texture), size_hint=(0.9, 0.9))
            popup.open()
            plt.close(fig)

        except Exception as e:
            popup = Popup(title="Error", content=Label(text=str(e)), size_hint=(0.8, 0.4))
            popup.open()

    def toggle_hill_climb_mode(self, instance=None):
      self.hill_climb_active = not self.hill_climb_active
      if self.hill_climb_active:
        self.hill_climb_btn.text = "Stop Hill Climb"
        self.climb_log = []
        self.climb_heart_rates = []
        self.climb_active = False
        self.climb_start_elevation = None
        self.climb_max_elevation = None
        self.climb_start_time = None
      else:
        self.hill_climb_btn.text = "Hill Climb Mode"

    def view_climb_history(self, instance=None):
        try:
            content = GridLayout(cols=1, spacing=10, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))

            for climb in self.climb_log:
                label = Label(
                text=f"Gain: {climb['gain']}m | Duration: {int(climb['duration'])}s | HR: {climb['avg_heart_rate']} BPM | Terrain: {climb['terrain']}",
                size_hint_y=None, height=40
            )
            content.add_widget(label)

            scroll = ScrollView(size_hint=(1, 1))
            scroll.add_widget(content)

            popup = Popup(title="Climb History", content=scroll, size_hint=(0.9, 0.9))
            popup.open()
        except Exception as e:
            popup = Popup(title="Error", content=Label(text=str(e)), size_hint=(0.8, 0.4))
            popup.open()     

    def view_top_climbs(self, instance=None):
        try:
            top_climbs = sorted(self.climb_log, key=lambda x: x['gain'], reverse=True)[:5]
            content = GridLayout(cols=1, spacing=10, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))

            for i, climb in enumerate(top_climbs, 1):
                label = Label(
                text=f"{i}. Gain: {climb['gain']}m | Duration: {int(climb['duration'])}s | HR: {climb['avg_heart_rate']} BPM | Terrain: {climb['terrain']}",
                size_hint_y=None, height=40
            )
            content.add_widget(label)

            scroll = ScrollView(size_hint=(1, 1))
            scroll.add_widget(content)

            popup = Popup(title="King of the Hill", content=scroll, size_hint=(0.9, 0.9))
            popup.open()
        except Exception as e:
            popup = Popup(title="Error", content=Label(text=str(e)), size_hint=(0.8, 0.4))
            popup.open()   

    def graph_climb_gain_vs_heart_rate(self, instance=None):
        ...           

    def graph_climb_gain_vs_heart_rate(self, instance=None):
        try:
            gains = [c['gain'] for c in self.climb_log if 'gain' in c]
            heart_rates = [c['avg_heart_rate'] for c in self.climb_log if 'avg_heart_rate' in c]

            if not gains or not heart_rates:
             raise ValueError("Missing gain or heart rate data.")

            fig, ax = plt.subplots()
            ax.plot(gains, heart_rates, marker='o')
            ax.set_xlabel("Elevation Gain (m)")
            ax.set_ylabel("Avg Heart Rate (BPM)")
            ax.set_title("Climb Gain vs Heart Rate")

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            im = CoreImage(buf, ext='png')

            popup = Popup(title="Gain vs Heart Rate", content=Image(texture=im.texture), size_hint=(0.9, 0.9))
            popup.open()
            plt.close(fig)

        except Exception as e:
            popup = Popup(title="Error", content=Label(text=str(e)), size_hint=(0.8, 0.4))
            popup.open()                      

        # Weather input
        self.weather_input = TextInput(
            hint_text='Enter Weather Conditions',
            size_hint=(1, 0.2),
            multiline=False
        )
        self.add_widget(self.weather_input)

        # Heart rate display
        self.heart_rate_label = Button(
            text="Heart Rate: -- BPM",
            size_hint=(1, 0.2),
            background_color=(0.8, 0.1, 0.1, 1)
        )
        self.add_widget(self.heart_rate_label)

        # Start/Stop buttons
        start_btn = Button(text="Start Ride", size_hint=(1, 0.2), background_color=(0, 0.6, 0.2, 1))
        start_btn.bind(on_press=self.start_ride)
        self.add_widget(start_btn)

        stop_btn = Button(text="Stop Ride", size_hint=(1, 0.2), background_color=(0.6, 0, 0.2, 1))
        stop_btn.bind(on_press=self.stop_ride)
        self.add_widget(stop_btn)

        # View history button
        history_btn = Button(text="View Ride History", size_hint=(1, 0.2), background_color=(0.2, 0.2, 0.6, 1))
        history_btn.bind(on_press=self.view_history)
        self.add_widget(history_btn)

    def select_vehicle(self, instance):
        self.selected_vehicle = instance.text
        print(f"Selected: {self.selected_vehicle}")

    def update_heart_rate(self, dt):
        bpm = get_fake_heart_rate()
        self.heart_rate_label.text = f"Heart Rate: {bpm} BPM"
        self.current_heart_rate = bpm
        self.heart_rate_log.append((datetime.now(), bpm))

    def start_ride(self, instance):
        if not self.selected_vehicle:
            print("Please select a vehicle first.")
            return

        g = geocoder.ip('me')
        self.ride_location = g.latlng if g.ok else [39.8283, -98.5795]
        self.ride_start_time = datetime.now()
        print(f"Ride started at {self.ride_start_time}")

        self.heart_rate_log = []
        self.heart_rate_event = Clock.schedule_interval(self.update_heart_rate, 5)
        self.update_heart_rate(0)
    def view_jump_history(self, instance=None):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        scroll = ScrollView(size_hint=(1, 1))
        inner = BoxLayout(orientation='vertical', size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        try:
            with open("jump_log.json", "r") as f:
                jumps = json.load(f)
        except:
            jumps = []

        for i, jump in enumerate(jumps):
            jump_text = f"{i+1}. {jump['height']}m | {jump['length']}m | {jump['force']}N | {jump['terrain']}"
            btn = Button(text=jump_text, size_hint_y=None, height=40)
            btn.bind(on_press=lambda inst, j=jump: self.graph_single_jump(j))
            inner.add_widget(btn)

            del_btn = Button(text="Delete", size_hint_y=None, height=30)
            del_btn.bind(on_press=lambda inst, idx=i: self.delete_jump(idx))
            inner.add_widget(del_btn)

        scroll.add_widget(inner)
        layout.add_widget(scroll)

        popup = Popup(title="Jump History", content=layout, size_hint=(0.9, 0.9))
        popup.open()

    def graph_single_jump(self, jump):
        plt.figure(figsize=(5, 3))
        plt.bar(['Height', 'Length', 'Force'], [jump['height'], jump['length'], jump['force']], color='green')
        plt.title(f"Jump on {datetime.fromtimestamp(jump['timestamp']).strftime('%Y-%m-%d %H:%M')}")
        plt.ylabel("Metric Value")
        plt.tight_layout()
        plt.show()

    def delete_jump(self, index):
        try:
            with open("jump_log.json", "r") as f:
                jumps = json.load(f)
            jumps.pop(index)
            with open("jump_log.json", "w") as f:
                json.dump(jumps, f, indent=4)
            print(f"Deleted jump at index {index}")
        except Exception as e:
            print(f"Error deleting jump: {e}")


        # Map style selection
        selected_style = self.map_style_spinner.text

        if selected_style == 'Stamen Terrain':
            tiles = 'Stamen Terrain'
            attr = None
        elif selected_style == 'OpenTopoMap':
            tiles = 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'
            attr = 'OpenTopoMap'
        elif selected_style == 'Mapbox Satellite':
            tiles = 'https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=pk.eyJ1Ijoid2VzbGV5OTYiLCJhIjoiY21nbzl1Y2tsMXpkYjJscTFtcTJyeDRvdiJ9.6DkvUJvVjkmu3EtxiD8gTw'
            attr = 'Mapbox'
        else:
            tiles = 'OpenStreetMap'
            attr = None

        m = folium.Map(location=self.ride_location, zoom_start=13, tiles=tiles, attr=attr)
        folium.Marker(self.ride_location, popup=f"{self.selected_vehicle} Ride Start").add_to(m)
        m.save("ride_map.html")
        webbrowser.open("ride_map.html")


    def stop_ride(self, instance):
        if not self.ride_start_time:
            print("No ride in progress.")
            return

        if self.heart_rate_event:
            self.heart_rate_event.cancel()
            self.heart_rate_event = None

        ride_end_time = datetime.now()
        duration = (ride_end_time - self.ride_start_time).total_seconds() / 60

        bpm_values = [t[1] for t in self.heart_rate_log]
        avg_bpm = round(sum(bpm_values) / len(bpm_values), 2) if bpm_values else 0
        max_bpm = max(bpm_values) if bpm_values else 0

        graph_filename = self.plot_heart_rate_trend()

        ride_data = {
            "vehicle": self.selected_vehicle,
            "start_time": self.ride_start_time.isoformat(),
            "end_time": ride_end_time.isoformat(),
            "duration_minutes": round(duration, 2),
            "location": self.ride_location,
            "terrain": self.terrain_spinner.text,
            "weather": self.weather_input.text,
            "heart_rate_bpm": self.current_heart_rate,
            "average_heart_rate_bpm": avg_bpm,
            "max_heart_rate_bpm": max_bpm,
            "heart_rate_graph": graph_filename
        }

        log_file = "ride_log.json"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(ride_data)

        with open(log_file, "w") as f:
            json.dump(logs, f, indent=4)

        print(f"Ride ended: {ride_data}")
        self.ride_start_time = None

        self.show_ride_summary(ride_data)
        self.heart_rate_log = []

    def plot_heart_rate_trend(self):
        if not self.heart_rate_log:
            return ""

        times = [t[0] for t in self.heart_rate_log]
        bpm_values = [t[1] for t in self.heart_rate_log]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        graph_filename = f"heart_rate_trend_{timestamp}.png"

        plt.figure(figsize=(8, 4))
        plt.plot(times, bpm_values, marker='o', color='red')
        plt.title("Heart Rate Trend During Ride")
        plt.xlabel("Time")
        plt.ylabel("BPM")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(graph_filename)
        plt.close()
        webbrowser.open(graph_filename)

        return graph_filename

    def show_ride_summary(self, ride_data):
        summary = (
            f"Vehicle: {ride_data['vehicle']}\n"
            f"Duration: {ride_data['duration_minutes']} minutes\n"
            f"Terrain: {ride_data['terrain']}\n"
            f"Weather: {ride_data['weather']}\n"
            f"Final Heart Rate: {ride_data['heart_rate_bpm']} BPM\n"
            f"Average Heart Rate: {ride_data['average_heart_rate_bpm']} BPM\n"
            f"Max Heart Rate: {ride_data['max_heart_rate_bpm']} BPM\n"
            f"Graph Saved As: {ride_data['heart_rate_graph']}"
        )

        popup = Popup(title="Ride Summary",
                      content=Label(text=summary),
                      size_hint=(0.8, 0.5))
        popup.open()

    def view_history(self, instance):
        log_file = "ride_log.json"
        if not os.path.exists(log_file):
            print("No ride history found.")
            return

        with open(log_file, "r") as f:
            logs = json.load(f)

        history_layout = BoxLayout(orientation='vertical', size_hint=(1, None))
        history_layout.bind(minimum_height=lambda layout, value: setattr(layout, 'height', value))

        for i, ride in enumerate(logs, 1):
            ride_text = (
                f"{i}. {ride['vehicle']} | {ride['start_time']} → {ride['end_time']}\n"
                f"   Terrain: {ride['terrain']} | Weather: {ride['weather']}\n"
                f"   Heart Rate: {ride['heart_rate_bpm']} BPM | "
                f"Avg: {ride.get('average_heart_rate_bpm', '--')} | "
                f"Max: {ride.get('max_heart_rate_bpm', '--')}"
            )

            ride_label = Label(text=ride_text, size_hint_y=None)
            ride_label.bind(texture_size=lambda instance, value: setattr(ride_label, 'height', value[1]))
            history_layout.add_widget(ride_label)

            graph_path = ride.get("heart_rate_graph")
            if graph_path and os.path.exists(graph_path):
                graph_btn = Button(text="View Graph", size_hint_y=None, height=40)
                graph_btn.bind(on_press=lambda _, path=graph_path: webbrowser.open(path))
                history_layout.add_widget(graph_btn)

        scroll = ScrollView(size_hint=(1, 0.8))
        scroll.add_widget(history_layout)
        self.add_widget(scroll)
    def view_history(self, instance):
        log_file = "ride_log.json"
        if not os.path.exists(log_file):
            print("No ride history found.")
            return

        with open(log_file, "r") as f:
            logs = json.load(f)

        self.clear_widgets()  # Clear previous widgets

        history_layout = BoxLayout(orientation='vertical', size_hint=(1, None))
        history_layout.bind(minimum_height=lambda layout, value: setattr(layout, 'height', value))

        for i, ride in enumerate(logs):
            ride_text = (
                f"{i+1}. {ride['vehicle']} | {ride['start_time']} → {ride['end_time']}\n"
                f"   Terrain: {ride['terrain']} | Weather: {ride['weather']}\n"
                f"   Heart Rate: {ride['heart_rate_bpm']} BPM | "
                f"Avg: {ride.get('average_heart_rate_bpm', '--')} | "
                f"Max: {ride.get('max_heart_rate_bpm', '--')}"
            )

            ride_label = Label(text=ride_text, size_hint_y=None)
            ride_label.bind(texture_size=lambda instance, value: setattr(ride_label, 'height', value[1]))
            history_layout.add_widget(ride_label)

            graph_path = ride.get("heart_rate_graph")
            if graph_path and os.path.exists(graph_path):
                graph_btn = Button(text="View Graph", size_hint_y=None, height=40)
                graph_btn.bind(on_press=lambda _, path=graph_path: webbrowser.open(path))
                history_layout.add_widget(graph_btn)

            delete_btn = Button(text="Delete Ride", size_hint_y=None, height=40, background_color=(0.8, 0.2, 0.2, 1))
            delete_btn.bind(on_press=lambda _, index=i: self.delete_ride(index))
            history_layout.add_widget(delete_btn)

        scroll = ScrollView(size_hint=(1, 0.8))
        scroll.add_widget(history_layout)
        self.add_widget(scroll)

    def delete_ride(self, index):
        log_file = "ride_log.json"
        if not os.path.exists(log_file):
            return

        with open(log_file, "r") as f:
            logs = json.load(f)

        if 0 <= index < len(logs):
            removed = logs.pop(index)
            with open(log_file, "w") as f:
                json.dump(logs, f, indent=4)
            print(f"Deleted ride: {removed['vehicle']} at {removed['start_time']}")
            self.view_history(None)


class PowerRideApp(App):
    def build(self):
        return VehicleSelector()

PowerRideApp().run()





