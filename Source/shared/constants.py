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
    "CRIT": 2**6,
    "HIGH": 2**4,
    "MIDD": 2**2,
    "NORM": 2**0,
    "NLIM": -1,
}

PRIOR_COLOR = {
    "CRIT": "red",
    "HIGH": "orange",
    "MIDD": "yellow",
    "NORM": "green",
    "NLIM": "blue",
}


def get_prior_weight(prior: str) -> int:
    return PRIOR_MAPPING.get(prior, 1)


def get_prior_color(prior: str | int) -> str:
    _ = [*[p for (p, sz) in PRIOR_MAPPING.items() if sz == prior], "NORM"]
    return PRIOR_COLOR.get(prior if isinstance(prior, str) else _[0], "green")
