"""
Regex-based text preprocessing phase, independent of most of the rest of the processor
(which is based on HTML).
Regex replacement rules are set using a C-like syntax:
#define foo bar

Supported flags:
* recursive: repeat all recursive rules until nothing changes
* end: apply at the very end, rather than by each line
* linestogether: apply to all lines together, rather than line by line (does nothing without end flag)
* literal: allow string literal style pattern and replacement, and don't use separator character
* id:example: assign an ID to the rule, so you can remove it later with #undef example
"""
import argparse
from collections import namedtuple
from itertools import count
from math import inf
from pathlib import Path
import shlex
import re

RegexRule = namedtuple('RegexRule', ['id', 'pattern', 'replacement', 'flags'])


def find_apply_regex_macros(raw: str) -> str:
    result_lines = []
    rules = []
    for line in raw.splitlines():
        original_line = line
        if line.startswith('#define'):
            rule_id = None
            flags = {}
            is_literal = False
            line = line[7:]
            match = re.match(r'\((([\w:]+)(?:,\s*([\w:]+))*)\)', line)
            if match:
                # use flags
                for flag_str in match[1].split(','):
                    flag_str = flag_str.strip()
                    if flag_str == 'recursive':
                        flags['recursive'] = True
                    elif flag_str == 'end':
                        flags['end'] = True
                    elif flag_str == 'linestogether':
                        flags['linestogether'] = True
                    elif flag_str == 'literal':
                        is_literal = True
                    elif flag_str.startswith('id:'):
                        rule_id = flag_str[3:]
                line = line[match.end():]
            if not line:
                raise ValueError(f'Incomplete #define line: {original_line}')
            if is_literal:
                pattern_str, replacement_str = shlex.split(line[1:])
            else:
                sep_char = line[0]
                _, pattern_str, replacement_str = line.split(sep_char)
            rules.append(RegexRule(
                id=rule_id,
                pattern=pattern_str,
                replacement=replacement_str,
                flags=flags
                ))
        elif line.startswith('#undef'):
            rule_id = line[7:].strip()
            rules = [rule for rule in rules if rule.id != rule_id]
        else:
            for round_number in count():
                changed = False
                for rule in rules:
                    max_repeats = 0 if rule.flags.get('end') else inf if rule.flags.get('recursive') else 1
                    if round_number >= max_repeats:
                        continue
                    old_line = line
                    line = re.sub(rule.pattern, rule.replacement, line)
                    changed |= old_line != line
                if not changed:
                    break
            result_lines.append(line)
    result = '\n'.join(result_lines)
    # apply end rules
    for round_number in count():
        changed = False
        for rule in rules:
            max_repeats = 0 if not rule.flags.get('end') else inf if rule.flags.get('recursive') else 1
            if round_number >= max_repeats:
                continue
            old_result = result
            if rule.flags.get('linestogether'):
                result = re.sub(rule.pattern, rule.replacement, result)
            else:
                result = '\n'.join(re.sub(rule.pattern, rule.replacement, line) for line in result.splitlines())
            changed |= old_result != result
        if not changed:
            break
    return result

def main():
    parser = argparse.ArgumentParser(
                    prog='regex_macro.py',
                    description='Run just the regex macro phase of the processor')
    parser.add_argument('-i', '--in-file', type=Path, required=True, help='Input file path')
    parser.add_argument('-o', '--out-file', type=Path, required=True, help='Output file path')
    args = parser.parse_args()
    
    with open(args.in_file) as file:
        raw = file.read()
    
    result = find_apply_regex_macros(raw)
    
    with open(args.out_file, 'w') as file:
        file.write(result)

if __name__ == '__main__':
    main()