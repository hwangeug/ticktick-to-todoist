#!/usr/bin/env python3

from ticktick import api
import pandas as pd
import re
import pytz
from getpass import getpass
from datetime import datetime, date


def ordinalize(number):
    if number == 1:
        return("1st")
    if number == 2:
        return("2nd")
    if number == 3:
        return("3rd")
    else:
        return("{}th".format(number))


def full_day_of_week(abbrev):
    dow_map = {
        "MO": "Monday",
        "TU": "Tuesday",
        "WE": "Wednesday",
        "TH": "Thursday",
        "FR": "Friday",
        "SA": "Saturday",
        "SU": "Sunday"
    }
    
    return(dow_map[abbrev])


def naturalize(rrule):
    if 'RRULE:' not in rrule:
        return ''

    # Parse TickTick RRULE into dict
    rrule = re.sub(r"^RRULE:", "", rrule)
    rrules = rrule.split(";")

    rule_dict = {}
    for r in rrules:
        name, value = r.split("=")
        rule_dict[name] = value

    # Reconstruct as an natural language statement

    # Figure out repeat period
    if rule_dict["FREQ"] == "DAILY":
        natural_period = "day"
    if rule_dict["FREQ"] == "WEEKLY":
        natural_period = "week"
    if rule_dict["FREQ"] == "MONTHLY":
        natural_period = "month"
    if rule_dict["FREQ"] == "YEARLY":
        natural_period = "year"

    # Convert INTERVAL + FREQ into natural language i.e. "every X <period>(s)"
    if int(rule_dict["INTERVAL"]) > 1:
        natural_period = "every {} {}s".format(int(rule_dict["INTERVAL"]), natural_period)
    else:
        natural_period = "every {}".format(natural_period)

    if rule_dict.get("BYDAY"):
        unparsed_byday = rule_dict.get("BYDAY")
        weekday_of_month, repeat_on_weekday = re.match(r"([0-9])?([A-Z]{2})", unparsed_byday).groups()
        
        # When there is an integer in front, e.g. "1SA", this means the nth Saturday of every month
        if weekday_of_month:
            return("on the {} {} of {}".format(ordinalize(int(weekday_of_month)), full_day_of_week(repeat_on_weekday), natural_period))
        # When there isn't an integer in front, e.g. "SA", this means Saturday every X weeks
        else:
            return(natural_period)

    else:
        return(natural_period)


def get_due_date(dd, tz):
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}\+\d{4}$", dd):
        dt = datetime.strptime(dd, '%Y-%m-%dT%H:%M:%S.%f%z')
        local_dt = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz))
        return(local_dt.strftime("%Y-%m-%d"))
    
    else:
        return ''


def ticktick_list_to_todoist_df(task_list):
    # Todoist and TickTick do subtasks a little differently
    # Pull nested task lists into their own tasks with an indent
    unnested = []
    for item in task_list:
        if len(item["items"]) == 0:
            unnested.append(item | {"level": 1})
        else:
            unnested.append(item | {"items": [], "level": 1})
            for sub_item in item["items"]:
                unnested.append(sub_item | {"level": 2})

    # Fill in minimal set of columns for Todoist CSV format
    if len(unnested) > 0:
        todoist_df = pd.DataFrame(unnested).\
            assign(# Fill in fields that may not be present in the TickTick list
                   content=lambda x: x.content.fillna('') if 'content' in x.columns else '',
                   dueDate=lambda x: x.dueDate.fillna('') if 'dueDate' in x.columns else '',
                   repeatFlag=lambda x: x.repeatFlag.fillna('') if 'repeatFlag' in x.columns else '').\
            assign(TYPE="task",
                   # Todoist CSV format won't allow for task notes, so pull any notes into task title
                   CONTENT=lambda x: [' - '.join([t, c]) if c else t for (t,c) in zip(x.title, x.content)],
                   PRIORITY=1,
                   INDENT=lambda x: x.level,
                   AUTHOR="",
                   RESPONSIBLE="",
                   DATE=lambda x: [" ".join([get_due_date(dd, tz), naturalize(rep)])
                                   for dd, tz, rep in zip(x.dueDate, x.timeZone, x.repeatFlag)],
                   DATE_LANG="en",
                   TIMEZONE="")\
            [["TYPE", "CONTENT", "PRIORITY", "INDENT", "AUTHOR", "RESPONSIBLE", "DATE", "DATE_LANG", "TIMEZONE"]]
    
        return(todoist_df)
    
    else:
        return None


def main():
    username = input("TickTick username: ")
    password = getpass(prompt="TickTick password: ")

    client = api.TickTickClient(username, password)  # Enter correct username and password

    # Build list of all tasks by project
    tasks_by_project = {}

    # Inbox isn't a "project"
    tasks_by_project["Inbox"] = client.get_by_fields(projectId=client.inbox_id)

    for project in client.get_by_fields(isOwner=True, search="projects"):
        tasks_by_project[project["name"]] = client.task.get_from_project(project["id"])

    # Convert task lists and write out to CSV
    for project, tasks in tasks_by_project.items():
        print('Exporting project "{}"'.format(project))
        df = ticktick_list_to_todoist_df(tasks)
        if df is not None:
            df.to_csv("{}.csv".format(project), index=False)


if __name__ == "__main__":
    main()
