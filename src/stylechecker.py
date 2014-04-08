"""
Module: stylechecker
--------------------
Stylechecker for student submissions. Takes points off for violations. The
regular expressions must be kept in sync with the ../check.py file.
"""
from CONFIG import STYLE_DEDUCTIONS
from errors import *
import os, sys, re

MAX_LINE_LENGTH = 80

S                   = "[^\(\) \t\n\r\f\v]"

header              = re.compile("-- \[Problem ([0-9])+([a-zA-Z])*\]")
result_header       = re.compile("-- \[Results\]")
bad_header          = re.compile("-- \[Problem([^\]])*\]")
comment             = re.compile("^--.|^/\*.|^\*/.")
tabs                = re.compile(r"\t+")
comma_space         = re.compile(",[^ ][^\n]")
operator_space      = re.compile(r"(.(\+|\-|\*|\<|\>|\=)" + S + ")" + \
                                 r"|(.(\=\=|\<\=|\>\=|\<\>)" + S + ")" + \
                                 r"|(" + S + "(\+|\-|\*|\<|\>|\=).)" + \
                                 r"|(" + S + "(\=\=|\<\=|\>\=|\<\>).)")
count_star          = re.compile("\(\*\)|\(DISTINCT \*\)")
double_quote        = re.compile("\"([^\"])*\"")
HAS_HEADER = False
MULTILINE_COMMENT = False
STARTED_RESULT = False

def check(f):
  """
  Function: check
  --------------
  Checks for style violations.

  f: The file to check.
  returns: The set of style violations for this file.
  """
  lines = f.readlines()
  errors = set()
  for i in range(len(lines)):
    line = lines[i][:-1]
    check_line(line, i + 1, errors)

  return errors


def deduct(style_errors):
  """
  Function: deduct
  ----------------
  Returns the amount of points to deduct for the set of style errors
  style_errors.
  """
  deductions = 0
  for error in list(style_errors):
    deductions += STYLE_DEDUCTIONS[type(error())]
  return deductions


def check_line(line, line_number, errors):
  """
  Function: check_line
  --------------------
  Checks a line of a file for style violations.

  line: The line to check.
  line_number: The line number of the line to check.
  errors: A set of errors so far.
  """
  global HAS_HEADER, MULTILINE_COMMENT, STARTED_RESULT
  is_bad_header = False

  if not len(line.strip()):
    return

  # Check for problem header formatting errors (cannot have code before a
  # problem header).
  if not HAS_HEADER and header.search(line):
    HAS_HEADER = True
  if not HAS_HEADER and line.strip().startswith("/*"):
    MULTILINE_COMMENT = True

  # If they started the results, ignore the 80 character limit.
  if result_header.search(line):
    STARTED_RESULT = True
  if STARTED_RESULT and header.search(line):
    STARTED_RESULT = False

  # Check for style mistakes.
  if bad_header.search(line) and not header.search(line):
    errors.add(BadHeaderError)
    is_bad_header = True
  if tabs.search(line):
    errors.add(UsedTabsError)
  if not STARTED_RESULT and len(line) > MAX_LINE_LENGTH:
    errors.add(LineTooLongError)
  if not MULTILINE_COMMENT and not comment.search(line):
    if comma_space.search(line) or operator_space.search(line) and not \
       reduce(lambda total, match: count_star.search(match[0]) and total, \
              operator_space.findall(line), True):
      errors.add(SpaceError)
    if double_quote.search(line):
      errors.add(DoubleQuoteError)

  # Continue checking for problem header mistakes.
  if not (HAS_HEADER or MULTILINE_COMMENT or is_bad_header or \
    comment.search(line.strip())):
    errors.add(CodeBeforeHeaderError)
  if line.strip().startswith("*/") or line.strip().endswith("*/"):
    MULTILINE_COMMENT = False