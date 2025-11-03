import geocoder

g = geocoder.ip('me')
print(f"Your location: {g.latlng}")
