#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pathlib
import argparse

import pandas as pd


# In[ ]:


# set up the argument parser
parser = argparse.ArgumentParser(description='Slurm stats')

parser.add_argument(
    "--acct",
    type=str,
    required=True,
    help="Path to the slurm accounts file"
)
parser.add_argument(
    "--jobs_stats",
    type=str,
    required=True,
    help="Path to the slurm jobs stats file"
)
parser.add_argument(
    "--days",
    type=int,
    required=True,
    help="Number of days to consider"
)
parser.add_argument(
    "--user",
    type=str,
    required=True,
    help="User to consider"
)
parser.add_argument(
    "--top_n",
    type=int,
    required=False,
    default=25,
    help="Number of top jobs to show"
)

args = parser.parse_args()

acct_file_path = pathlib.Path(args.acct).resolve(strict=True)
jobs_file_path = pathlib.Path(args.jobs_stats).resolve(strict=True)
days = args.days
user = args.user
n = args.top_n


# In[ ]:


# read the file the first row has the column names and the rest of the rows are the data

df = pd.read_csv(acct_file_path, sep='|', header=0, skiprows=1)
# drop the columns that are not needed
df = df.drop(columns=[
    'Cluster',
    'Account',
    # 'Login',
    'TRES Name'
    ])

# order the data by used
df = df.sort_values(by='Used', ascending=False)
df.reset_index(drop=True, inplace=True)
# remove NaN values
df = df.dropna()
# remove 0 values
df = df[df.Used != 0]

# pretty print the top 15 users and their usage
print(f"Top {n} users by usage for the last {days} days")
print(df.head(n))


# In[ ]:


# load the job stats file
# sep by tab
df = pd.read_csv(jobs_file_path, skiprows=[0,2], sep='\t', header=0)
while "  " in df.columns[0]:
    df.columns = df.columns.str.replace('  ', ' ')
# replace "  " in all rows and columns with " "
df = df.replace('\s+', ' ', regex=True)
# split all the columns
new_columns = df.columns[0].split(' ') + ['wait_units']
# # # split the contents of the first column
df = df[df.columns[0]].str.split(' ', expand=True)
# rename the columns
df.columns = new_columns
# cast types
df['jobid'] = df['jobid'].astype(str)
df['jobname'] = df['jobname'].astype(str)
df['partition'] = df['partition'].astype(str)
df['qos'] = df['qos'].astype(str)
df['account'] = df['account'].astype(str)
df['cpus'] = df['cpus'].astype(int)
df['state'] = df['state'].astype(str)
df['start-date-time'] = df['start-date-time'].astype(str)
df['elapsed'] = df['elapsed'].astype(str)
df['wait'] = df['wait'].astype(float)
df['wait_units'] = df['wait_units'].astype(str)


# In[ ]:


# calculate the total wait time in hours
# get summary statistics
print(df['wait'].sum())
print(f"{df['wait'].sum()} hours in queue for the last {days} days")


# In[ ]:


# get counts for jobs on each partition types
print(f"Job counts by partition for the last {days} days")
print(df['partition'].value_counts())

