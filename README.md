# `ticktick-to-todoist`

## Description

This is a script to convert the data from your [TickTick](https://www.ticktick.com) account into [Todoist](https://www.todoist.com) [project template](https://todoist.com/help/articles/how-to-format-your-csv-file-so-you-can-import-it-into-todoist) files that you can use to transfer your todo list items.

The following are not implemented in this script, but is possible to do within the CSV spec:

- Task notes
- Priority

This Works On My Data.  However, task repetition parsing may not be comprehensively implemented - I don't have a spec to work off of.

## Usage

Run `./ticktick-to-todoist.py` in a directory that you would like to write your Todoist CSV files to.  Input your username and password.  

## Requirements

- [ticktick-py](https://github.com/lazeroffmichael/ticktick-py)
- [pytz](https://pythonhosted.org/pytz/)
- [pandas](https://pandas.pydata.org/)
- Python 3.9

A TickTick account.  OAuth is not supported.
