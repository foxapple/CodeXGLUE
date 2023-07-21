def keyset_result(iter, params, **kwargs):

    import csv
    import sys

    def _column_map(keyset, name):
        if keyset.get('column_mappings', None):
            mappings = keyset['column_mappings']
            if name in mappings and mappings[name]:
                return mappings[name]
        return name

    last_keyset_name = None
    writer = csv.writer(sys.stdout)
    for keys, values in iter:
        keyset_name = keys[0]
        if last_keyset_name != keyset_name:
            keyset = params.keysets[keyset_name]
            columns = keyset['key_parts'][1:] + keyset['value_parts']
            mapped = [_column_map(keyset, column) for column in columns]
            writer.writerow(mapped)
            last_keyset_name = keyset_name
        data = keys[1:] + values
        row = [unicode(x).encode('utf-8') for x in data]
        writer.writerow(row)


def reduce_result(iter, **kwargs):

    import csv
    import sys

    def default_flush_callback(stream):
        stream.flush()
        return stream

    output_stream = kwargs.get('output_stream', sys.stdout)
    flush_schedule = kwargs.get('flush_schedule', 5000)
    flush_callback = kwargs.get('flush_callback', default_flush_callback)

    writer = csv.writer(output_stream)
    count = 0
    for keys, values in iter:
        data = keys + values
        row = [unicode(x).encode('utf-8') for x in data]
        writer.writerow(row)
        count += 1
        if count > flush_schedule:
            output_stream = flush_callback(output_stream)
            count = 0
    flush_callback(output_stream)
