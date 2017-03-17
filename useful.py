import math

def prj_WMtoLL(x,y):
  # Check if coordinate out of range for Web Mercator
  # 20037508.3427892 is full extent of Web Mercator
  if (abs(x) > 20037508.3427892) or (abs(y) > 20037508.3427892):
    print("coordinates provided were out of range; maximum range for Web Mercator is +/-20037508.343")
    return

  semimajorAxis = 6378137.0  # WGS84 spheriod semimajor axis

  latitude = (1.5707963267948966 - (2.0 * math.atan(math.exp((-1.0 * y) / semimajorAxis)))) * (180 / math.pi)
  longitude = ((x / semimajorAxis) * 57.295779513082323) - \
              ((math.floor((((x / semimajorAxis) * 57.295779513082323) + 180.0) / 360.0)) * 360.0)

  return [longitude, latitude]

def prj_LLtoWM(lon, lat):
  return

