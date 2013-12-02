from CONFIG import SQL_DEDUCTIONS
import dbtools
import iotools
import mysql.connector
from response import Response

class Grade:
  """
  Class: Grade
  ------------
  Handles the grading of different types of problems. Runs the different types
  of tests on that problem.
  """

  def __init__(self, specs):
    # The specifications for this assignment.
    self.specs = specs


  def get_function(self, test):
    """
    Function: get_function
    ----------------------
    Finds the right function to call on for the specified test.

    test: The test to find the right function for.
    returns: A function object.
    """
    test_type = test["type"]
    if test_type == "select":
      return self.select
    elif test_type == "create":
      return self.create
    elif test_type == "stored-procedure":
      return self.sp
    # TODO


  def deduct(points, error):
    """
    Function: deduct
    ----------------
    Deduct from points depending on the error.

    points: The points to deduct from.
    error: The error.
    returns: The new amount to deduct.
    """
    
    
  def grade(self, problem, response, graded, cursor):
    """
    Function: grade
    ---------------
    Runs all of the tests for a particular problem and computes the number
    of points received.

    problem: The problem specification.
    response: The student's response.
    graded: The graded problem output.
    cursor: The database cursor.

    returns: The number of points received for this problem.
    """
    # Problem definitions.
    num = problem["number"]
    num_points = problem["points"]

    # Print out some things before running tests.
    self.pretest(problem, response, graded)

    # The number of points this student has received so far on this problem.
    got_points = num_points

    # Run each test for the problem.
    for test in problem["tests"]:
      lost_points = 0
      graded_test = {"errors": [], "deductions": [], "success": False}
      graded["tests"].append(graded_test)

      try:
        # Figure out what kind of test it is and call the appropriate function.
        f = self.get_function(test)
        lost_points += f(test, response, graded_test, cursor)

        # Apply any other deductions.
        if graded_test.get("deductions"):
          for deduction in graded_test["deductions"]:
            (lost, desc) = SQL_DEDUCTIONS[deduction]
            graded["errors"].append(desc)
            lost_points += lost

      # If there was a MySQL error, print out the error that occurred and the
      # code that caused the error.
      except mysql.connector.errors.ProgrammingError as e:
        graded["errors"].append("MYSQL ERROR " + str(e))
        lost_points += test["points"]

      got_points -= lost_points
      graded_test["got_points"] = test["points"] - lost_points
      #except Exception as e:
      #  print "TODO", str(e)
        # TODO handle

    # Get the total number of points received.
    got_points = (got_points if got_points > 0 else 0)
    graded["got_points"] = got_points
    return got_points


  def pretest(self, problem, response, graded):
    """
    Function: pretest
    -----------------
    Check for certain things before running the tests and print them out.
    This includes:
      - Comments
      - Attaching results of query
      - Checking their SQL for certain keywords
      - Printing out their actual SQL

    problem: The problem specification.
    response: The student's response.
    graded: The graded problem output.
    """
    # Comments, query results, and SQL.
    graded["comments"] = response.comments
    graded["submitted-results"] = response.results
    graded["sql"] = response.sql

    # Check for keywords.
    if problem.get("keywords"):
      missing = False
      missing_keywords = []
      for keyword in problem["keywords"]:
        if keyword not in response.sql:
          missing = True
          missing_keywords.append(keyword)
      if missing:
        graded["errors"].append("MISSING KEYWORDS " + ", ".join(missing_keywords))

    # TODO take points off for missing keywords?


  def select(self, test, response, graded, cursor):
    """
    Function: select
    ----------------
    Runs a test SELECT statement and compares it to the student's SELECT
    statement. Possibly checks for the following things:
      - Order of rows
      - Order of columns
      - Whether or not derived relations are renamed

    test: The test to run.
    response: The student's response.
    graded: The graded test output.
    cursor: The database cursor.

    returns: The number of points to deduct.
    """
    success = True
    deductions = 0
    test_points = test["points"]

    # TODO make sure they aren't doing SQL injection
    expected = dbtools.run_query(test.get("setup"), test["query"], cursor)
    actual = dbtools.run_query(test.get("setup"), response.sql, cursor)

    # If we don't need to check that the results are ordered, then sort the
    # results for easier checking.
    if not test.get("ordered"):
      expected.results = sorted(expected.results)
      actual.results = sorted(actual.results)

    # If we don't need to check that the columns are ordered in the same way,
    # then sort each tuple for easier checking.
    if not test.get("column-order"):
      expected.results = [tuple(sorted(x)) for x in expected.results]
      actual.results = [tuple(sorted(x)) for x in actual.results]

    # Compare the student's code to the results.
    if expected.results != actual.results:
      graded["expected"] = expected.output
      graded["actual"] = actual.output
      deductions = test_points

      # Check to see if they forgot to ORDER BY.
      if test.get("ordered"):
        eresults = sorted(expected.results)
        aresults = sorted(actual.results)
        if aresults == eresults:
          deductions = 0
          graded["deductions"].append("orderby")

      # See if they chose the wrong column order.
      if test.get("column-order"):
        eresults = [tuple(sorted(x)) for x in expected.results]
        aresults = [tuple(sorted(x)) for x in actual.results]
        if eresults == aresults:
          print "here"
          deductions = 0
          graded["deductions"].append("columnorder")

      success = False

    # Check to see if they named aggregates.
    # TODO check for other things? must contain a certain word in col name?
    if test.get("rename"):
      for col in actual.col_names:
        if col.find("(") + col.find(")") != -2:
          graded["deductions"].append("renamecolumns")
          success = False
          break

    # TODO more or fewer columns?
    graded["success"] = success
    return deductions


  def create(self, test, response, graded, cursor):
    """
    Function: create
    ----------------
    TODO

    test: The test to run.
    response: The student's response.
    cursor: The database cursor.

    returns: True if the test passed, False otherwise.
    """
    # TODO check for drop tables?
    # TODO check for comments?

    graded["success"] = True
    # TODO create table statements are just printed.
    return 0


  def sp(self, test, response, graded, cursor):
    """
    Function: sp
    ------------
    Tests a stored procedure by calling the procedure and checking the contents
    of the table before and after.

    test: The test to run.
    response: The student's response.
    graded: The graded test output.
    cursor: The database cursor.

    returns: The number of points to deduct.
    """
    
    
    return 0
    
    
    
    
