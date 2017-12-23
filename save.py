def get_key(buffer, index, long=False):
    """
    this function gets the key to unlock the inner strength of human kind.
    :param buffer:
    :param index:
    :param long:
    :return:
    """
    script_nb = list()
    while buffer[index] != '>':
        script_nb.append(buffer[index])
        index += 1
    if long:
        # TODO: do these things in a cleaner and automated way
        if script_nb[-1] != '0':
            script_nb[-1] = str(int(script_nb[-1]) - 1)  # passing from 9 to 10
        else:
            script_nb[-1] = '9'
            if script_nb[-2] != '0':
                script_nb[-2] = str(int(script_nb[-2]) - 1)  # passing from 99 to 100
            else:
                script_nb[-2] = '9'
                if script_nb[-3] != '0':
                    script_nb[-3] = str(int(script_nb[-3]) - 1)  # passing from 999 to 1000
                else:
                    script_nb[-3] = '9'
                    script_nb[-4] = str(int(script_nb[-4]) - 1)
        script_nb.insert(0, '0')
        script_nb.append('.txt')
    return ''.join(script_nb)


def right_key(key, buffer, index):
    """
    right key ? or not...?
    :param key:
    :param buffer:
    :param index:
    :return:
    """
    script_nb = get_key(buffer, index)
    if key.find(script_nb) != -1:
        return True
    return False


def length_is_okay(line):
    if line.find('<CLT') != -1:
        for i in range(99):
            if i < 10:
                line = line.replace('<CLT 0' + str(i) + '>', '')
            else:
                line = line.replace('<CLT ' + str(i) + '>', '')
        line = line.replace('<CLT>', '')
    if line.find('\n') == -1:
        if len(line) > 64:
            return False
        else:
            return True
    else:
        tab = line.split('\n')
        for single_line in tab:
            if len(single_line) > 64:
                return False
            else:
                return True
