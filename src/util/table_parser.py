def parse_tabular_data(table_data: str, required_headers=()) -> list[dict]:
    if not isinstance(table_data, str) or not table_data.strip():
        raise ValueError("表格内容为空或不是文本")

    lines = table_data.splitlines()
    headers = lines[0].rstrip('\t').split('\t')
    if not all(headers) or len(set(headers)) != len(headers):
        raise ValueError("表格表头包含空字段或重复字段")
    missing_headers = [header for header in required_headers if header not in headers]
    if missing_headers:
        raise ValueError(f"表格缺少必要字段: {', '.join(missing_headers)}")

    rows = []
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        values = line.split('\t')
        while len(values) > len(headers) and values[-1] == '':
            values.pop()
        if len(values) != len(headers):
            raise ValueError(f"表格第{line_number}行列数与表头不一致")
        rows.append(dict(zip(headers, values)))
    return rows
