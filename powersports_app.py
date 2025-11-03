# powersports_app.py
# Optimized for Cursor: Run in Cursor editor (Ctrl+R to execute, Ctrl+I for AI suggestions).
# To add features, type in Cursor: "Add [feature, e.g., eBike battery]" and accept suggestions.
# Requires: Python 3.12+, numpy (pip install numpy), folium (optional for maps: pip install folium)

import math
import json
from datetime import datetime
import numpy as np
try:
    import folium
    MAP_ENABLED = True
except ImportError:
    MAP_ENABLED = False
    print("Install folium for route maps: pip install folium")

# Vehicle configs (edit in vehicles.json for easy tweaks without code changes)
try:
    with open('vehicles.json', 'r') as f:
        VEHICLES = json.load(f)
except FileNotFoundError:
    VEHICLES = {
        'dirtbike': {'name': 'Dirtbike', 'max_g_lateral': 1.5, 'cal_factor': 1.2, 'met': 6.0},
        'atv': {'name': 'ATV', 'max_g_lateral': 1.2, 'cal_factor': 1.1, 'met': 5.5},
        'utv': {'name': 'UTV', 'max_g_lateral': 1.0, 'cal_factor': 1.0, 'met': 5.0},
        'snowmobile': {'name': 'Snowmobile', 'max_g_lateral': 1.3, 'cal_factor': 1.15, 'met': 5.8},
        'ebike': {'name': 'Electric Bike', 'max_g_lateral': 0.8, 'cal_factor': 0.9, 'met': 4.5}
    }
    with open('vehicles.json', 'w') as f:
        json.dump(VEHICLES, f, indent=2)
        print("Created vehicles.json - edit for custom vehicle settings")

def calculate_g_force(vehicle_type: str, speed_kmh: float, radius_m: float = 50, jump_height: float = 0) -> tuple[float, str]:
    """
    Calculate G-force (lateral + vertical) for a ride.
    Args:
        vehicle_type: From VEHICLES dict (e.g., 'dirtbike').
        speed_kmh: Average speed in km/h.
        radius_m: Tightest turn radius (meters).
        jump_height: Max jump height (meters).
    Returns:
        Tuple of total G-force and safety alert.
    Cursor Tip: Type 'modify g-force calc' to tweak (e.g., add roll angle).
    """
    try:
        v = speed_kmh / 3.6  # Convert to m/s
        g_lateral = (v ** 2) / (radius_m * 9.81)  # Centripetal: v²/rg
        g_vertical = (2 * jump_height) / (9.81 ** 2) if jump_height > 0 else 0  # Free fall
        total_g = math.sqrt(g_lateral**2 + g_vertical**2)
        vehicle = VEHICLES[vehicle_type]
        alert = "WARNING: High G-force!" if total_g > vehicle['max_g_lateral'] else "Safe"
        return total_g, alert
    except (KeyError, ZeroDivisionError) as e:
        print(f"Error in G-force calc: {e}. Check vehicle_type or radius.")
        return 0.0, "Error"

def health_monitor(hr_input: float, duration_min: float, weight_kg: float, vehicle_type: str) -> dict:
    """
    Health metrics: Calories, HR zone, recovery score (0-100).
    Args:
        hr_input: Average heart rate (bpm).
        duration_min: Ride duration (minutes).
        weight_kg: Rider weight (kg).
        vehicle_type: From VEHICLES dict.
    Returns:
        Dict with calories, HR zone, recovery, and advice.
    Cursor Tip: Type 'add health metric' to extend (e.g., VO2 max).
    """
    try:
        met = VEHICLES[vehicle_type]['met']  # METs per vehicle
        calories = met * weight_kg * (duration_min / 60) * VEHICLES[vehicle_type]['cal_factor']
        
        # HR zones (assume age 30, max HR = 190)
        max_hr = 190
        zone = 'Fat Burn' if hr_input < max_hr * 0.7 else 'Aero' if hr_input < max_hr * 0.85 else 'Peak'
        recovery = max(0, 100 - (hr_input / max_hr * 100))
        advice = 'Hydrate & rest if <70' if recovery < 70 else 'Strong ride!'
        return {
            'calories_burned': round(calories),
            'hr_zone': zone,
            'recovery_score': round(recovery),
            'advice': advice
        }
    except KeyError as e:
        print(f"Error in health calc: {e}. Check vehicle_type.")
        return {'error': 'Invalid vehicle'}

def trace_route(points: list[tuple[float, float]]) -> tuple[float, str]:
    """
    Trace route: Calculate distance (Haversine), generate GPX.
    Args:
        points: List of (lat, lon) tuples.
    Returns:
        Tuple of distance (km) and GPX string.
    Cursor Tip: Type 'add map feature' to extend (e.g., elevation).
    """
    try:
        def haversine(p1, p2):
            lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
            lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            return 6371 * 2 * math.asin(math.sqrt(a))  # km
        
        distance = sum(haversine(points[i], points[i+1]) for i in range(len(points)-1))
        
        gpx = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="PowerRide AI">
<trk><name>PowerRide Route</name><trkseg>
{''.join(f'<trkpt lat="{p[0]}" lon="{p[1]}"><time>{datetime.now().isoformat()}</time></trkpt>' for p in points)}
</trkseg></trk></gpx>"""
        
        if MAP_ENABLED:
            m = folium.Map(location=points[0], zoom_start=12)
            folium.PolyLine(points, color='blue', weight=5).add_to(m)
            m.save('route_map.html')
            print("Map saved: route_map.html")
        
        return distance, gpx
    except Exception as e:
        print(f"Error in route tracing: {e}. Check points format.")
        return 0.0, ""

def main():
    """
    Main app loop: Collect inputs, compute metrics, save session.
    Cursor Tip: Type 'add feature to main' to extend (e.g., AI nutrition plan).
    """
    print("=== PowerRide AI Coach: Powersports Edition ===")
    vehicle_type = input("Select vehicle (dirtbike/atv/utv/snowmobile/ebike): ").lower()
    if vehicle_type not in VEHICLES:
        print("Invalid! Default to dirtbike.")
        vehicle_type = 'dirtbike'
    
    # Inputs (sim sensors)
    try:
        speed = float(input("Avg speed (km/h): "))
        duration = float(input("Ride duration (mins): "))
        hr_avg = float(input("Avg heart rate (bpm): "))
        radius = float(input("Tightest turn radius (m, ~50 for trails): "))
        jump_h = float(input("Biggest jump height (m, 0 if none): "))
        weight = float(input("Your weight (kg): "))
        
        # GPS points (min 2 for route)
        print("\nEnter at least 2 GPS points (lat,lon):")
        points = []
        while len(points) < 2:
            try:
                lat = float(input("Lat: "))
                lon = float(input("Lon: "))
                points.append((lat, lon))
            except ValueError:
                print("Invalid lat/lon. Try again.")
        
        # Compute
        g_total, g_alert = calculate_g_force(vehicle_type, speed, radius, jump_h)
        health_data = health_monitor(hr_avg, duration, weight, vehicle_type)
        dist, gpx = trace_route(points)
        
        # Output
        print("\n=== Ride Summary ===")
        print(f"Vehicle: {VEHICLES[vehicle_type]['name']}")
        print(f"G-Force: {g_total:.2f}G ({g_alert})")
        print(f"Health: {health_data['calories_burned']} cal burned | Zone: {health_data['hr_zone']} | Recovery: {health_data['recovery_score']}% - {health_data['advice']}")
        print(f"Route: {dist:.2f} km traced. GPX in ride_log.json")
        
        # Save session
        session = {
            'timestamp': datetime.now().isoformat(),
            'vehicle': vehicle_type,
            'g_force': g_total,
            'health': health_data,
            'distance_km': dist,
            'gpx': gpx
        }
        with open('ride_log.json', 'a') as f:
            json.dump(session, f, indent=2)
            f.write('\n')
        print("Log appended: ride_log.json")
        
        # AI Advice (sim OpenAI)
        advice = f"Post-ride tips for {VEHICLES[vehicle_type]['name']}: {health_data['advice']} Refuel with 50g carbs if G >1.0G."
        print(f"\nAI Coach: {advice}")
        
    except ValueError as e:
        print(f"Input error: {e}. Use numbers for speed, duration, etc.")
    except Exception as e:
        print(f"Unexpected error: {e}. Debug in Cursor (Ctrl+Shift+D).")

if __name__ == "__main__":
    main()