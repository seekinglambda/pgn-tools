import sys
import os
import re
from mod_pgn_subtree import pgn_subtree

def insert_braces(text):
    # Find all the occurrances of the braced string using re.finditer
    brace_matches = list(re.finditer(r'\{(.*?)\}', text, flags=re.DOTALL))

    # Iterate through all the matches (in reversed order because inserting stuff messes up the matches completely)
    for brace_match in reversed(brace_matches):
        start_pos = brace_match.start()
        end_pos = brace_match.end()

        # Find the position of the first [% within the braces
        percent_match = re.search(r'\[%', brace_match.group(1), flags=re.DOTALL)
        if percent_match is None:
            continue

        percent_pos = percent_match.start() + start_pos + 1

        comment_text = text[start_pos + 1:percent_pos].strip()

        # Insert "} {" at the position of the [% , if and only if the text before is non-empty
        if comment_text:
            text = text[:percent_pos] + "} { " + text[percent_pos:]

    return text

def format_path(path):
    last_sep = path.rfind(os.path.sep)
    if last_sep != -1:
        dir_path = path[:last_sep]
        second_last_sep = dir_path.rfind(os.path.sep)
        if second_last_sep != -1:
            return ".." + path[second_last_sep:]
        else:
            return path
    else:
        return path

def log_info(text):
    if output_file != "-":
        print(text)

#----------------------------------------------

try:
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    if len(sys.argv) >= 4:
        locations = sys.argv[3:]
    else:
        locations = ""
except IndexError:
    raise SystemExit(f"Usage: {sys.argv[0]} <INPUT_FILE> <OUTPUT_FILE> [<TRANSPOSITION_DIRECTORY_OR_FILE>...]")

if input_file == "-":
    pgn = "".join(sys.stdin.read())
else:
    f = open(input_file, encoding="utf-8")
    pgn = f.read()


transposition_files = []
transposition_dirs = []
for location in locations:
    if os.path.isfile(location):
        transposition_files.append(location)
    elif os.path.isdir(location):
        transposition_dirs.append(location)
    else:
        log_info(f"Error. \"{location}\" doesn't exist.")
        exit()

# Add the input file as a transposition file and the directory of the input file as a transposition directory
input_file_dir = os.path.dirname(os.path.realpath(input_file)) + os.path.sep
transposition_dirs.append(input_file_dir)
transposition_files.append(input_file)


# Print all transposition files and dirs
log_info(f"  Input file: \"{format_path(input_file)}\"")
log_info(f"  Output file: \"{format_path(output_file)}\"")
log_info(f"  Global transposition files and dirs:")
for file in transposition_files:
    log_info(f"    \"{format_path(file)}\"")
for dir in transposition_dirs:
    log_info(f"    \"{format_path(dir)}\"")


# Looking for a comment like so:
#   Transposition: "Some text", bla bla moves bla bla[, filename.pgn]                       # filename is optional
#   Transposition: "Open Catalan", 1.d4 Nf6 2.c4 e6 3.g3 d5 4.Bg2 dxc4 5.Nf3, d4_catalan.pgn
#   Transposition: "Open Catalan", 1.d4 Nf6 2.c4 e6 3.g3 d5 4.Bg2 dxc4 5.Nf3
regex = re.compile(r'\{\s*Transposition:\s*\"(.*?)\",(.*?)(,(.*?))?\}', re.DOTALL)

match = regex.search(pgn)
num_matches = 0
num_errors = 0
while (match):
    info = match.group(1).strip()
    moves = match.group(2).strip()
    match_file = match.group(4).strip() if match.group(4) else ""

    first_non_space = pgn[match.end():].strip()[0]

    replacement = ""

    log_info(f"  Transposition:  [ {info} ]\n   Target moves:      {moves}     File: {format_path(match_file)}")

    # If a specific transposition file in the match is given, look for it in all transposition directories
    if match_file:
        for dir in transposition_dirs:
            path = dir + match_file
            if os.path.isfile(path):
                replacement = pgn_subtree(path, moves)
                if replacement:
                    break
                else:
                    log_info(f"      Not found in {path}")
    
    # Now look in the current file and transposition files provided by the caller of this script
    if not replacement:
        for file in transposition_files:
            replacement = pgn_subtree(file, moves)
            if replacement:
                break
            else:
                log_info(f"      Not found in {file}")

    # If a transposition file has not been found by now, give an error
    if not replacement:
        error_msg = f"  ERROR {num_errors + 1}: Unable to find a move [{info}] with moves [{moves}] in any transposition file."
        log_info(error_msg)
        replacement = "{ " + error_msg + " }"
        num_errors += 1

    elif first_non_space not in [")", "(", "*"]:
        error_msg = f"  ERROR {num_errors + 1}: The move at transposition [{info}] with moves [{moves}] in {input_file} is not empty. \"{first_non_space}\""
        log_info(error_msg)
        replacement = "{ " + error_msg + " }"
        num_errors += 1

    pgn = pgn[:match.start()] + replacement + pgn[match.end():]

    match = regex.search(pgn)
    num_matches += 1


look_for = "Transposition:"
remaining = pgn.count(look_for)
log_info(f"  ----------------------------------------------")
log_info(f"  Number of transpositions resolved: {num_matches - num_errors} / {num_matches}")
log_info(f"  *** WARNING! Number of remaining \"{look_for}\" occcurrancies: {remaining}") if remaining > 0 else ""
log_info(f"  ----------------------------------------------")

if output_file == "-" and num_errors == 0:
    print(pgn)
else:
    f = open(output_file, "w", encoding="utf-8")
    f.write(pgn)
    f.close()    

