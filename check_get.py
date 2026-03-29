with open('d:/bus manag/app.py') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'def api_timings_get' in line:
            print(''.join(lines[i-2:i+15]))
            break
