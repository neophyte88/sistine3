import datetime


def str_interval_to_datetime(str_interval):
    if str_interval.endswith("h"):
        minutes = 60 * int(str_interval.replace("h", ""))
    elif str_interval.endswith("m"):
        minutes = int(str_interval.replace("m", ""))
    else:
        raise ValueError("Invalid string interval")

    return datetime.datetime.now() - datetime.timedelta(minutes=minutes)
