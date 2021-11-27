from datetime import datetime




def timestamp_to_date(timestamp):
    timestamp = timestamp / 1000
    dt= datetime.fromtimestamp(timestamp)
    print(dt)
    return dt


timestamp_to_date(1637892515000)
