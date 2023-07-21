'''Adding support to termcolor.
Failures and errors are red and sucessful is green.


>>> SupportToTermcolor.run()
False
>>> colored_output2 = """Story: Support to termcolor
...   As a pyhistorian commiter
...   I want to have support to colored output
...   So that the output becomes more readable
... 
...   Scenario 1: Green color
... """+green_output+"""
...   Scenario 2: Red color
... """+red_output+"""
...   Scenario 3: Green and red colors
... """+green_and_red_output+"""
...   Ran 3 scenarios with 3 failures, 0 errors and 0 pending steps
... """
>>> checker.check_output(colored_output2, output.getvalue(), doctest.ELLIPSIS)
True
'''

from pyhistorian import *
from pyhistorian.output import colored
from should_dsl import *
from cStringIO import StringIO
import os
import doctest

HERE = os.path.dirname(__file__) + '/colors.py'
checker = doctest.OutputChecker()

class GreenColor(Scenario):
    @Given('I want my output colored and it pass')
    def nothing(self):
        pass

    @Then('I have green messages')
    def nothing2(self):
        pass

class RedColor(Scenario):
    @Given('I want my output colored and it fails')
    def fail1(self):
         'this scenario' |should_be| 'red colored'

    @Then('I have red messages')
    def fail2(self):
        'this fail color' |should_be| 'red'


class GreenAndRedColors(Scenario):
   @Given('I want my output colored (green and red)')
   def nothing(self):
       pass

   @Then('I have green message')
   def green_message(self):
       pass

   @Then('I have red message')
   def red_message(self):
       'this step' |should_be| 'red'


def red_colored(text):
    return colored(text, color='red')

def green_colored(text):
    return colored(text, color='green')

output = StringIO()

class SupportToTermcolor(Story):
    """As a pyhistorian commiter
       I want to have support to colored output
       So that the output becomes more readable"""
    output = output
    colored = True
    scenarios = (GreenColor, RedColor, GreenAndRedColors)

green_output = green_colored('\
    Given I want my output colored and it pass   ... OK\n')+ \
  green_colored('\
    Then I have green messages   ... OK\n')

red_output = red_colored('\
    Given I want my output colored and it fails   ... FAIL\n')+ \
  red_colored('\
    Then I have red messages   ... FAIL\n') +\
  red_colored('\n  Failures:\n')+\
  red_colored("""    File "%(here)s", line ..., in fail1
      'this scenario' |should_be| 'red colored'
    ...
    ShouldNotSatisfied: 'this scenario' is not 'red colored'

""" % {'here': HERE})+\
  red_colored("""    File "%(here)s", line ..., in fail2
      'this fail color' |should_be| 'red'
    ...
    ShouldNotSatisfied: 'this fail color' is not 'red'

""" % {'here': HERE})
green_and_red_output = green_colored('\
    Given I want my output colored (green and red)   ... OK\n')+\
  green_colored('\
    Then I have green message   ... OK\n') + \
  red_colored('\
    And I have red message   ... FAIL\n') +\
  red_colored('\n  Failures:\n') + \
  red_colored("""    File "%(here)s", line ..., in red_message
      'this step' |should_be| 'red'
    ...
    ShouldNotSatisfied: 'this step' is not 'red'

""" % {'here': HERE})
