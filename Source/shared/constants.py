STATUS_SIGNAL = {
    "accept": "[accept]",
    "invalid": "[invalid]",
    "terminate": "[terminate]",
    "interrupt": "[interrupt]",
}

DAT_SIGNAL = {
    "data": "DATA",
    "done": "DONE",
    "list": "LIST",
    "error": "ERROR",
}

PRIOR_MAPPING = {
    "NLIM": -1,
    "CRIT": 2**3,
    "HIGH": 2**2,
    "MIDD": 2**1,
    "NORM": 1,
}
