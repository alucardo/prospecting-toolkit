import re


def extract_cid_from_maps_url(url):
    """
    Wyciaga parametr CID z linku Google Maps.
    Obsluguje:
    - https://maps.google.com/?cid=1234567890
    - https://www.google.com/maps?cid=1234567890
    - https://www.google.com/maps/place/Nazwa/@lat,lng/data=...!1s0x...:0x...
    Zwraca 'cid:NUMBER' lub None jesli nie znaleziono.
    """
    if not url:
        return None
    # Format bezposredni: ?cid=1234567890
    match = re.search(r'[?&]cid=(\d+)', url)
    if match:
        return f"cid:{match.group(1)}"
    # Format hex w data: !1s0x...:0x...
    match = re.search(r'!1s0x[0-9a-f]+:(0x[0-9a-f]+)', url)
    if match:
        try:
            cid = int(match.group(1), 16)
            return f"cid:{cid}"
        except Exception:
            pass
    return None
