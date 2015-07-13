from gridcheck import *


def get_filter_data(dcs):
    filter_data = []
    for dc in dcs:
        url = 'http://{0}:{1}/clients'.format(dc['url'], dc['port'])
        if 'user' and 'password' in dc:
            r = requests.get(url, auth=(dc['user'], dc['password']))
        else:
            r = requests.get(url)
        data = r.json()
        r.close()

        for i in data:
            for s in i['subscriptions']:
                if s not in filter_data:
                    filter_data.append(s)

    assert type(filter_data) == list
    return filter_data


def get_data(dc):
    url = 'http://{0}:{1}/results'.format(dc['url'], dc['port'])

    if 'user' and 'password' in dc:
        r = requests.get(url, auth=(dc['user'], dc['password']))
    else:
        r = requests.get(url)

    data = r.json()
    r.close()
    return data


def get_clients(dc):
    url = 'http://{0}:{1}/clients'.format(dc['url'], dc['port'])

    if 'user' and 'password' in dc:
        r = requests.get(url, auth=(dc['user'], dc['password']))
    else:
        r = requests.get(url)

    data = r.json()
    r.close()
    return data


def get_stashes(dc):
    url = 'http://{0}:{1}/stashes'.format(dc['url'], dc['port'])

    if 'user' and 'password' in dc:
        r = requests.get(url, auth=(dc['user'], dc['password']))
    else:
        r = requests.get(url)

    data = r.json()
    r.close()
    return data


def agg_data(dc, data, stashes, client_data=None, filters=None):
    """
    Aggregates json data and returns count of ok, warn, crit
    :param data: raw json data
    :return: dc_name, l_ok, l_warn, l_crit
    """
    ok = 0
    warn = 0
    crit = 0
    down = 0
    ack = 0
    _filtered = []

    if filters and len(filters) > 0:
        filters = filters.split(',')

    if filters is not None and client_data is not None:
        for c in client_data:
            for sub in c['subscriptions']:
                if sub in filters:
                    _filtered.append(c['name'])

    for i in data:

        if len(_filtered) > 0:

            if i['client'] in _filtered:

                if i['check']['status'] == 0 and not i['check']['name'] == "keepalive":
                    ok += 1
                if i['check']['status'] == 1 and not i['check']['name'] == "keepalive":
                    if not check_stash(stashes, i['client'], i['check']['name']):
                        warn += 1
                    else:
                        ack += 1
                if i['check']['status'] == 2 and not i['check']['name'] == "keepalive":
                    if not check_stash(stashes, i['client'], i['check']['name']):
                        crit += 1
                    else:
                        ack += 1

                if i['check']['name'] == "keepalive" and i['check']['status'] == 2:
                    if not check_stash(stashes, i['client'], i['check']['name']):
                        # we cannot currently apply filters as keepalive checks do not have subscribers/subscriptions
                        down += 1
                    else:
                        ack += 1

        elif filters is None:

            if i['check']['status'] == 0 and not i['check']['name'] == "keepalive":
                ok += 1

            if i['check']['status'] == 1 and not i['check']['name'] == "keepalive":
                if not check_stash(stashes, i['client'], i['check']['name']):
                    warn += 1
                else:
                    ack += 1

            if i['check']['status'] == 2 and not i['check']['name'] == "keepalive":
                if not check_stash(stashes, i['client'], i['check']['name']):
                    crit += 1
                else:
                    ack += 1

            if i['check']['name'] == "keepalive" and i['check']['status'] == 2:
                if not check_stash(stashes, i['client'], i['check']['name']):
                    # we cannot currently apply filters as keepalive checks do not have subscribers/subscriptions
                    down += 1
                else:
                    ack += 1

    return {"name": dc['name'], "ok": ok, "warning": warn, "critical": crit, "down": down, "ack": ack}


def agg_host_data(data, stashes, client_data=None, filters=None):
    """
    returns: a dict of {"hostname": [list,of,alert,statuses], "hostname2": [list,of,alert,statuses]}
    """

    _data = data
    _stashes = stashes
    _clients = client_data
    retdata = {}

    if filters and len(filters) > 0:
        filters = filters.split(',')

    if _clients is not None:
        for c in _clients:
            if filters and len(filters) > 0:
                for f in filters:
                    if f in c['subscriptions']:
                        _host = c['name']
                        retdata[_host] = []
                        break
            else:
                _host = c['name']
                retdata[_host] = []
    else:
        for check in _data:
            _host = check['client']
            retdata[_host] = []

    for check in _data:
        _host = check['client']
        if check['check']['status'] and check['check']['name'] != 'keepalive':
            if _host in retdata:
                if not check_stash(_stashes, _host, check['check']['name']):
                    retdata[_host].append(check['check']['status'])

        if check['check']['status'] and check['check']['name'] == 'keepalive':
            if _host in retdata:
                retdata[_host].append(-1)

    assert type(retdata) == dict

    return retdata
