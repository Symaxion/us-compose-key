#!/usr/bin/env python
# coding=utf-8

#
# Author: Frank Erens
#

import unicodedata
import os
import re
import sys
import xml.etree.ElementTree as ET

KEYLAYOUT_FILE      = "U.S. with Compose Key.bundle/Contents/Resources/"\
                      "U.S. with Compose Key.keylayout"
CPSKEY_ROOT         = "Compose Key"
CPSKEY_PREFIX       = CPSKEY_ROOT

reload(sys)
sys.setdefaultencoding('utf-8')

def read_keylayout():
    with open(KEYLAYOUT_FILE, 'r') as f:
        return f.read().replace('\n', '')

def remove_illegal_entities(doc):
    return re.sub(r'&#x00[0-1][0-9A-F];', r'', doc)

def parse_keylayout():
    # return ET.parse(KEYLAYOUT_FILE).getroot()
    return ET.ElementTree(ET.fromstring(
        remove_illegal_entities(read_keylayout())
    ))

def get_actions_xml():
    return parse_keylayout().findall("actions/action")

def when_xml_to_dict(w):
    return {
        'state': w.attrib["state"],
        'output': w.attrib.get("output"),
        'next': w.attrib.get("next"),
    }

def find_key_for_action(action):
    try:
        return {
            'key': action.find("when[@state='none']").attrib.get("output"),
            'whens': [
                when_xml_to_dict(w) for \
                w in action.findall("when") \
                if w.attrib["state"].startswith(CPSKEY_PREFIX)
            ]
        }
    except:
        return {}

def find_keys_for_actions():
    return [find_key_for_action(a) for a in get_actions_xml() if a != {}]

def sequences_for_state(aks, state):
    sequences = []

    for ak in aks:
        for w in ak['whens']:
            if w['state'] == state:
                result = { 'key': ak['key'] }
                if w['output'] is not None:
                    result['output'] = w['output']
                else:
                    result['next'] = sequences_for_state(aks, w['next'])
                sequences.append(result)

    return sequences

def all_sequences():
    return sequences_for_state(find_keys_for_actions(), CPSKEY_ROOT)

def flatten_sequence_list(seq):
    if 'next' in seq:
        # TODO: Turn this into a list comprehension?
        ret = []
        for nseq in seq['next']:
            fnseq = flatten_sequence_list(nseq)
            for s in fnseq:
                ret.append([seq['key']] + s)
        return ret
    else:
        return [[seq['key'], seq['output']]]

def flatten_sequence(seq):
    if seq == []:
        return {}
    else:
        return {
            'sequence': seq[:-1],
            'output': seq[-1],
        }

def flatten_all_sequences():
    return sorted(
        filter(
            lambda x: x != {},
            [
                flatten_sequence(item) for sublist in
                [
                    flatten_sequence_list(seq) \
                    for seq in all_sequences()
                ] for item in sublist
            ]
        ),
        key=lambda x: x['sequence']
    )

def escape_str(s):
    if s == " ":
        return "(space)"
    elif s in ['|', '$', '`', '\\', '[', ']']:
        return "\\" + s
    elif s == '"':
        return "&quot;"
    else:
        return None

def show_char_extra(char):
    return char

def show_char(char):
    return escape_str(char) or show_char_extra(char)

def show_key_extra(key):
    # FIXME: Hack to support Option + Key in one sequence
    # TODO: How to read this from keylayout file?
    if key == u'Æ':
        return u'⌥&quot;'
    else:
        return key

def show_key(key):
    return escape_str(key) or show_key_extra(key)

def unicodename(output):
    try:
        return unicodedata.name(unicode(output))
    except:
        try:
            return {
                u'': "*APPLE LOGO*",
                u'n̈': "*LATIN SMALL LETTER N WITH DIAERESIS*",
                u'N̈': "*LATIN CAPITAL LETTER N WITH DIAERESIS*",
                u'T̈': "*LATIN CAPITAL LETTER T WITH DIAERESIS*",
            }[output]
        except:
            return ""

def generate_table_entry(seq):
    return "| %-6s | %-7s | %-7s | %-7s | %-37s |" % (
        show_char(seq['output']),
        show_key(seq['sequence'][0]),
        show_key(seq['sequence'][1]),
        show_key(seq['sequence'][2]) if len(seq['sequence']) == 3 else "",
        unicodename(seq['output'])
    )

def generate_combination_table():
    sys.stdout.write("""
| Symbol |  Key 1  |  Key 2  |  Key 3  |      Unicode Name / *Description*     |
|:------:|:-------:|:-------:|:-------:|:--------------------------------------|
""")
    for seq in flatten_all_sequences():
        print generate_table_entry(seq)


if __name__ == "__main__":
    generate_combination_table()
