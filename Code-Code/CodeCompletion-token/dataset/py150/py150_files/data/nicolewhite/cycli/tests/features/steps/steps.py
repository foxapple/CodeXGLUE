from __future__ import unicode_literals

import time

import pexpect
from behave import given, when, then


def expect_exact(context, expected):
    context.cli.expect_exact(expected, timeout=2)

@given(u"I start cycli")
def step_start_cycli(context):
    context.cli = pexpect.spawnu("cycli -u neo4j -p password")

@given(u"The prompt is visible")
def step_prompt_visible(context):
    time.sleep(1)
    expect_exact(context, "> ")

@when(u"I ask for my env vars")
def step_get_env_vars(context):
    context.cli.sendline("env")

@given(u"I set an env var equal to a string")
def step_set_param_string(context):
    context.cli.sendline("export name=\"Nicole\"")

@when(u"I ask for the string env var by key")
def step_get_param_string_key(context):
    context.cli.sendline("env[\"name\"]")

@then(u"I should see the string env var without the key")
def step_get_param_string_key(context):
    expect_exact(context, "Nicole")

@then(u"I should see the string env var")
def step_get_param_string(context):
    expect_exact(context, "name=Nicole")

@given(u"I set an env var equal to a number")
def step_set_param_number(context):
    context.cli.sendline("export age=24")

@then(u"I should see the numeric env var")
def step_get_param_number(context):
    expect_exact(context, "age=24")

@given(u"I set an env var equal to a boolean")
def step_set_param_boolean(context):
    context.cli.sendline("export blonde=True")

@then(u"I should see the boolean env var")
def step_get_param_boolean(context):
    expect_exact(context, "blonde=True")

@given(u"I set an env var equal to a Python list comprehension")
def step_set_param_list(context):
    context.cli.sendline("export evens=[x for x in range(10) if x % 2 == 0]")

@then(u"I should see the list env var")
def step_get_param_list(context):
    expect_exact(context, "evens=[0, 2, 4, 6, 8]")

@given(u"I start cycli in read-only mode")
def step_start_cycli_read_only(context):
    context.cli = pexpect.spawnu("cycli -u neo4j -p password -r")

@when(u"I execute a write query")
def step_execute_write_query(context):
    context.cli.sendline("CREATE (n) RETURN n;")

@then(u"I should be told I'm in read-only mode")
def step_tell_read_only(context):
    expect_exact(context, "Query aborted. You are in read-only mode.")

@when(u"I ask to see the labels")
def step_get_labels(context):
    context.cli.sendline("schema-labels")

@given(u"I add a node with a label")
def step_add_node_with_label(context):
    context.cli.sendline("CREATE (p:Person);")

@when(u"I refresh the schema")
def step_refresh_schema(context):
    context.cli.sendline("refresh")

@then(u"I should see the new label")
def step_see_new_label(context):
    for expected_line in ["Labels", "------", "Person"]:
        expect_exact(context, expected_line)