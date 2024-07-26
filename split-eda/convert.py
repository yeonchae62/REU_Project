# Converts EDA data from (stdin or an input file) in a specific format to a
# machine-readable .json file that can be processed by SplitEDA.

import argparse
import json
import re
import sys

description = '''
Convert EDA data to a consistent machine-readable .json format.

The input data should be in one of two formats, described below:

Format 1: Target data located from cell F3 to G61.
Data grouped by: slope / flat -> trial 1 / 2 -> single-view / multi-view / HMD -> task.
Example: https://docs.google.com/spreadsheets/d/1-May6DuTs2R8P_4KFMpte4-PzWe2duCD8SjorBGL-LI/edit?gid=0#gid=0

Format 2: Target data located from cell I3 to J76.
Data grouped by: demolition / baseline -> none / mv1 / mv2 / discrete / continuous -> trial 1 / 2 -> task.
Example: https://docs.google.com/spreadsheets/d/1GWZHWgC9oJYVgeqqYfWR0hhytyENWrFX8bSpuFErVlk/edit?pli=1&gid=0#gid=0
'''

def unwrap_or_none(s: str) -> str or None:
    '''
    Returns the string if it is not empty, otherwise returns None.
    '''
    return s if s else None

def split_row(s: str) -> list[str]:
    '''
    Splits a string by commas or tabs and returns a list of the resulting strings.
    '''
    return re.split(',|\t', s)

def fill(data: list[str], target_len: int) -> list[str]:
    '''
    Fills a list with empty strings until it reaches the target length.
    '''
    return data + [''] * (target_len - len(data))

def format_1(data: str) -> list[dict]:
    # order of data:
    # 1. single-view, slope, trial 1
    # 2. multiple-view, slope, trial 1
    # 3. HMD, slope, trial 1
    # 4. single-view, slope, trial 2
    # 5. multiple-view, slope, trial 2
    # 6. HMD, slope, trial 2
    # 7. single-view, flat, trial 1
    # 8. multiple-view, flat, trial 1
    # 9. HMD, flat, trial 1
    # 10. single-view, flat, trial 2
    # 11. multiple-view, flat, trial 2
    # 12. HMD, flat, trial 2

    # each group of data contains 4 lines, each line is a start and end time
    # line 1: ignored
    # line 2: pickup start, pickup end
    # line 3: obstacle start, obstacle end
    # line 4: dump start, dump end

    # go through each data and extract the start and end times, categorize by the above order
    out = []

    order = [
        ('single-view', 'slope', 1),
        ('multiple-view', 'slope', 1),
        ('HMD', 'slope', 1),
        ('single-view', 'slope', 2),
        ('multiple-view', 'slope', 2),
        ('HMD', 'slope', 2),
        ('single-view', 'flat', 1),
        ('multiple-view', 'flat', 1),
        ('HMD', 'flat', 1),
        ('single-view', 'flat', 2),
        ('multiple-view', 'flat', 2),
        ('HMD', 'flat', 2),
    ]

    lines = data.split('\n')

    # 12 (groups) * 5 (lines per group, including bottom blank line)
    group_lines = 12 * 5
    for i in range(0, group_lines, 5):
        path = order[i // 5]
        group = list(map(lambda s: fill(split_row(s), 2), lines[i:i + 5]))

        # get the start and end times
        pickup = (unwrap_or_none(group[1][0]), unwrap_or_none(group[1][1]))
        obstacle = (unwrap_or_none(group[2][0]), unwrap_or_none(group[2][1]))
        dump = (unwrap_or_none(group[3][0]), unwrap_or_none(group[3][1]))

        out.append({
            'meta': {
                'path': {
                    'kind': path[0],
                    'ground': path[1],
                    'trial': path[2],
                },
            },
            'pickup': pickup,
            'obstacle': obstacle,
            'dump': dump
        })

    return {
        'format': 1,
        'data': out,
    }

def format_2(data: str) -> list[dict]:
    # order of data:
    # 1. none, demolition, trial 1
    # 2. mv1 (side view), demolition, trial 1
    # 3. mv2 (top view), demolition, trial 1
    # 4. discrete, demolition, trial 1
    # 5. continuous, demolition, trial 1
    # 6. none, demolition, trial 2
    # 7. mv1 (side view), demolition, trial 2
    # 8. mv2 (top view), demolition, trial 2
    # 9. discrete, demolition, trial 2
    # 10. continuous, demolition, trial 2
    # 11. none, baseline, trial 1
    # 12. mv1 (side view), baseline, trial 1
    # 13. mv2 (top view), baseline, trial 1
    # 14. discrete, baseline, trial 1
    # 15. continuous, baseline, trial 1
    # 16. none, baseline, trial 2
    # 17. mv1 (side view), baseline, trial 2
    # 18. mv2 (top view), baseline, trial 2
    # 19. discrete, baseline, trial 2
    # 20. continuous, baseline, trial 2

    # data groups 1-10 contain 3 lines, each line is a start and end time
    # line 1: pickup start, pickup end
    # line 2: obstacle start, obstacle end
    # line 3: dump start, dump end

    # data groups 11-20 contain 6 lines, each line is also a start and end time
    # line 1: 1st trial start, 1st trial end
    # line 2: 2nd trial start, 2nd trial end
    # ...

    # go through each data and extract the start and end times, categorize by the above order
    out = []

    order = [
        ('none', 'demolition', 1),
        ('mv1', 'demolition', 1),
        ('mv2', 'demolition', 1),
        ('discrete', 'demolition', 1),
        ('continuous', 'demolition', 1),
        ('none', 'demolition', 2),
        ('mv1', 'demolition', 2),
        ('mv2', 'demolition', 2),
        ('discrete', 'demolition', 2),
        ('continuous', 'demolition', 2),
        ('none', 'baseline', 1),
        ('mv1', 'baseline', 1),
        ('mv2', 'baseline', 1),
        ('discrete', 'baseline', 1),
        ('continuous', 'baseline', 1),
        ('none', 'baseline', 2),
        ('mv1', 'baseline', 2),
        ('mv2', 'baseline', 2),
        ('discrete', 'baseline', 2),
        ('continuous', 'baseline', 2),
    ]

    lines = data.split('\n')

    # process data group 1-10
    # 10 (groups) * 4 (lines per group, including bottom blank line)
    group_1_lines = 10 * 4
    for i in range(0, group_1_lines, 4):
        path = order[i // 4]
        group = list(map(lambda s: fill(split_row(s), 2), lines[i:i + 4]))

        # get the start and end times
        pickup = (unwrap_or_none(group[0][0]), unwrap_or_none(group[0][1]))
        obstacle = (unwrap_or_none(group[1][0]), unwrap_or_none(group[1][1]))
        dump = (unwrap_or_none(group[2][0]), unwrap_or_none(group[2][1]))

        out.append({
            'meta': {
                'path': {
                    'visual_guide': path[0],
                    'environment': path[1],
                    'trial': path[2],
                },
            },
            'pickup': pickup,
            'obstacle': obstacle,
            'dump': dump
        })

    # process data group 11-20
    # 5 (groups) * 7 (lines per group, including bottom blank line)
    group_2_lines = 5 * 7
    for i in range(group_1_lines, group_1_lines + group_2_lines, 7):
        path = order[(i - group_1_lines) // 7 + 10]
        group = list(map(lambda s: fill(split_row(s), 2), lines[i:i + 7]))

        # get the start and end times for each trial
        trials = [
            (unwrap_or_none(group[0][0]), unwrap_or_none(group[0][1])),
            (unwrap_or_none(group[1][0]), unwrap_or_none(group[1][1])),
            (unwrap_or_none(group[2][0]), unwrap_or_none(group[2][1])),
            (unwrap_or_none(group[3][0]), unwrap_or_none(group[3][1])),
            (unwrap_or_none(group[4][0]), unwrap_or_none(group[4][1])),
            (unwrap_or_none(group[5][0]), unwrap_or_none(group[5][1])),
        ]

        out.append({
            'meta': {
                'path': {
                    'visual_guide': path[0],
                    'environment': path[1],
                    'trial': path[2],
                },
            },
            'trials': trials,
        })

    return {
        'format': 2,
        'data': out,
    }

def main():
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-f', '--format', type=int, choices=[1, 2], required=True,
                        help='The format of the input data (1 or 2), see description for details.')
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Path to input file (default: stdin)')
    parser.add_argument('output', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='Path to output file (default: stdout)')

    args = parser.parse_args()

    input_file = args.input
    output_file = args.output

    with input_file as infile, output_file as outfile:
        data = infile.read()

        if args.format == 1:
            out = format_1(data)
        elif args.format == 2:
            out = format_2(data)

        json.dump(out, outfile, indent=4)

if __name__ == '__main__':
    main()
