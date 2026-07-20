#!/usr/bin/env python
# coding: utf-8

# In[1]:


import argparse
import pathlib
from pprint import pprint

import matplotlib.pyplot as plt
import pandas as pd

try:
    cfg = get_ipython().config
    in_notebook = True
except NameError:
    in_notebook = False


# In[2]:


def print_times(df, wait_column):
    if df[wait_column].sum() > 24 * 365:
        wait = df[wait_column].sum() / 24 / 365
        wait_units = "years"
    elif df[wait_column].sum() > 24:
        wait = df[wait_column].sum() / 24
        wait_units = "days"
    else:
        wait = df[wait_column].sum()
        wait_units = "hours"
    # round to two decimal places
    wait = round(wait, 2)
    return wait, wait_units


def SU_to_compute_time(SU):
    if SU > 24 * 365:
        compute_time = SU / 24 / 365
        compute_units = "years"
    elif SU > 24:
        compute_time = SU / 24
        compute_units = "days"
    else:
        compute_time = SU
        compute_units = "hours"
    # round to two decimal places
    compute_time = round(compute_time, 2)
    return compute_time, compute_units


def elapsed_time_to_hours(elapsed_time):
    if "-" in elapsed_time:
        days = int(elapsed_time.split("-")[0])
        elapsed_time = elapsed_time.split("-")[1]
        hours, minutes, seconds = elapsed_time.split(":")
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
        total_hours = days * 24 + hours + minutes / 60 + seconds / 3600
    else:
        hours, minutes, seconds = elapsed_time.split(":")
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
        total_hours = hours + minutes / 60 + seconds / 3600

    return total_hours


# In[3]:


stats_file_dir = pathlib.Path("../slurm_stats_files").resolve(strict=True)
results_dir = pathlib.Path("../results").resolve()
results_dir.mkdir(exist_ok=True, parents=True)


# In[4]:


if not in_notebook:
    # set up the argument parser
    parser = argparse.ArgumentParser(description="Slurm stats")

    parser.add_argument(
        "--days", type=int, required=True, help="Number of days to consider"
    )
    parser.add_argument("--user", type=str, required=True, help="User to consider")
    parser.add_argument(
        "--top_n",
        type=int,
        required=False,
        default=25,
        help="Number of top jobs to show",
    )
    args = parser.parse_args()

    days = args.days
    user = args.user
    n = args.top_n
else:
    days = 10000
    user = "mlippincott@xsede.org"
    n = -1


acct_file_path = pathlib.Path("../slurm_stats_files/").resolve(strict=True)
jobs_file_path = pathlib.Path("../slurm_stats_files/").resolve(strict=True)
# find the most recent file in the directory
acct_files = list(acct_file_path.glob("*accounts*"))
job_files = list(jobs_file_path.glob("*jobs*"))
# sort
acct_files.sort(reverse=True)
job_files.sort(reverse=True)
acct_file_path = acct_files[0]  # get the most recent accounts file
jobs_file_path = job_files[0]  # get the most recent jobs file


# In[5]:


# read the file the first row has the column names and the rest of the rows are the data

df = pd.read_csv(acct_file_path, sep="|", header=0, skiprows=1)
# drop row if "SU" or Cluster is in the cluster columns
df = df[~df["Cluster"].str.contains("SU|Cluster", na=False)]
# drop login if na
df = df.dropna(subset=["Login"])
# drop the columns that are not needed
df = df.drop(
    columns=[
        "Cluster",
        "TRES Name",
    ]
)
df["Used"] = df["Used"].astype(int)


# In[6]:


user_df = (
    df.groupby(
        [
            "Login",
            "Proper Name",
            "Account",
        ]
    )
    .sum()
    .reset_index()
).drop_duplicates(subset=["Login"], keep="first")
user_df = (
    user_df.groupby(
        [
            "Login",
            "Proper Name",
        ]
    )
    .sum()
    .reset_index()
)


# In[7]:


user_df.insert(
    2,
    "Institution",
    user_df["Account"].apply(
        lambda x: (
            "CSU"
            if "csu" in x.lower()
            else (
                "AMC"
                if "amc" in x.lower()
                else (
                    "UCB"
                    if "ucb" in x.lower()
                    else "RMACC" if "rmacc" in x.lower() else "Other"
                )
            )
        )
    ),
)
df.insert(
    2,
    "Institution",
    df["Account"].apply(
        lambda x: (
            "CSU"
            if "csu" in x.lower()
            else (
                "AMC"
                if "amc" in x.lower()
                else (
                    "UCB"
                    if "ucb" in x.lower()
                    else "RMACC" if "rmacc" in x.lower() else "Other"
                )
            )
        )
    ),
)

# order the data by used
user_df = user_df.sort_values(by="Used", ascending=False)
# remove NaN values
user_df = user_df.dropna()
# remove 0 values
user_df = user_df[user_df.Used != 0]
user_df.drop(columns=["Account"], inplace=True)
user_df.reset_index(drop=True, inplace=True)
institution_df = df.groupby(["Institution"]).sum().reset_index()
institution_df.drop(columns=["Login", "Proper Name", "Account"], inplace=True)
institution_df.sort_values(by="Used", ascending=False, inplace=True)


# In[8]:


user_df = user_df.sort_values(by="Used", ascending=False)


# In[9]:


# get the total usage for the user
SUs = user_df[user_df["Login"] == user]["Used"].sum()
# show all rows

# drop the login column
df = df.drop(columns=["Login"])
# pretty print the top 15 users and their usage
if not in_notebook:
    if n == -1:
        pd.set_option("display.max_rows", df.shape[0])
        pprint(f"Total SUs for each institution for the last {days} days")
        pprint(institution_df)
        pprint(f"Top {len(user_df)} users by usage for the last {days} days")
        pprint(user_df)

    else:
        pd.set_option("display.max_rows", n)
        pprint(f"Total SUs for each institution for the last {days} days")
        pprint(institution_df.head(n))
        pprint(f"Top {n} users by usage for the last {days} days")
        pprint(user_df.head(n))


# write the data to a file
user_df.to_csv(
    f"../results/{acct_file_path.stem.strip('_accounts_date')}_top_users.csv",
    index=False,
)


# In[10]:


# load the job stats file
# sep by tab
df = pd.read_csv(jobs_file_path, skiprows=[0, 2], sep="\t", header=0)
while "  " in df.columns[0]:
    df.columns = df.columns.str.replace("  ", " ")
    df = df.replace("  ", " ", regex=True)
# replace "  " in all rows and columns with " "

# split all the columns
new_columns = df.columns[0].split(" ") + ["wait_units"]
# # # split the contents of the first column
df = df[df.columns[0]].str.split(" ", expand=True)
# rename the columns
df.columns = new_columns
# cast types
df["jobid"] = df["jobid"].astype(str)
df["jobname"] = df["jobname"].astype(str)
df["partition"] = df["partition"].astype(str)
df["qos"] = df["qos"].astype(str)
df["account"] = df["account"].astype(str)
df["cpus"] = df["cpus"].astype(int)
df["state"] = df["state"].astype(str)
df["start-date-time"] = df["start-date-time"].astype(str)
df["elapsed"] = df["elapsed"].astype(str)
df["wait"] = df["wait"].astype(float)
df["wait_units"] = df["wait_units"].astype(str)
df["hours_computed"] = df["elapsed"].apply(elapsed_time_to_hours)

# get the compute and wait time for the user for each partition type
hours_df = df.groupby("partition").agg({"hours_computed": "sum", "wait": "sum"})

hours_df["wait_ratio"] = hours_df["wait"] / hours_df["hours_computed"]
print(f"Compute and wait time for {user} by partition for the last {days} days")
print(hours_df)


# In[11]:


# calculate the total wait time in hours
# get summary statistics
wait, wait_units = print_times(df, "wait")
compute_time, compute_time_units = print_times(df, "hours_computed")
su_time, su_time_units = SU_to_compute_time(SUs)
print(
    f"{user} has waited a total of {wait} {wait_units} in queue in the last {days} days"
)
print(
    f"{user} has used a total of {compute_time} {compute_time_units} of compute time in the last {days} days"
)
print(
    f"{user} has used a total of {SUs} SUs in the last {days} days for a total of {su_time} {su_time_units} if 1 SU = 1 hour of compute time"
)


# In[12]:


n_users_by_institution = (
    (user_df.groupby("Institution").agg(Users=("Login", "count"), SUs=("Used", "sum")))
    .reset_index("Institution")
    .sort_values(by="SUs", ascending=False)
)
n_users_by_institution["SUs_normalized_by_users"] = (
    n_users_by_institution["SUs"] / n_users_by_institution["Users"]
)


# In[13]:


if in_notebook:

    plt.figure(figsize=(20, 6))
    plt.subplot(131)
    plt.bar(
        n_users_by_institution["Institution"],
        n_users_by_institution["SUs"],
        color=["blue", "orange", "green", "red", "purple"],
    )
    plt.title(f"SUs by Institution \nfor the last {days} days")
    plt.xlabel("Institution")
    plt.ylabel("SUs")
    plt.subplot(132)
    plt.bar(
        n_users_by_institution["Institution"],
        n_users_by_institution["Users"],
        color=["blue", "orange", "green", "red", "purple"],
    )
    plt.title(f"Number of Users by Institution \nfor the last {days} days")
    plt.xlabel("Institution")
    plt.ylabel("Number of Users")
    plt.subplot(133)
    plt.bar(
        n_users_by_institution["Institution"],
        n_users_by_institution["SUs_normalized_by_users"],
        color=["blue", "orange", "green", "red", "purple"],
    )
    plt.title(f"Normalized SUs by Institution \nfor the last {days} days")
    plt.xlabel("Institution")
    plt.ylabel("Normalized SUs (SUs / Users)")
    plt.show()


# In[16]:


if in_notebook:

    # plot the top 25 users by usage
    plt.figure(figsize=(10, 6))
    plt.bar(
        user_df.head(25)["Proper Name"],
        user_df.head(25)["Used"],
    )
    plt.title(f"Top 25 Users by Usage for the last {days} days")
    # make the x-axis labels vertical
    plt.xticks(rotation=50, ha="right")
    plt.xlabel("User")
    plt.ylabel("Used")
    plt.show()


# In[30]:


if in_notebook:

    top_user = user_df.iloc[0]
    top_5_users = user_df.head(5)
    top_10_users = user_df.head(10)
    top_25_users = user_df.head(25)
    top_50_users = user_df.head(50)
    top_100_users = user_df.head(100)

    top_200_users = user_df.head(200)
    user_df_sorted = user_df.sort_values("Used", ascending=True).reset_index(drop=True)
    cum_used = user_df_sorted["Used"].cumsum()

    x_top1 = (cum_used >= top_user["Used"]).idxmax() + 1
    y_top1 = top_user["Used"]

    x_top5 = (cum_used >= top_5_users["Used"].sum()).idxmax() + 1
    y_top5 = top_5_users["Used"].sum()

    x_top10 = (cum_used >= top_10_users["Used"].sum()).idxmax() + 1
    y_top10 = top_10_users["Used"].sum()

    x_top25 = (cum_used >= top_25_users["Used"].sum()).idxmax() + 1
    y_top25 = top_25_users["Used"].sum()

    x_top50 = (cum_used >= top_50_users["Used"].sum()).idxmax() + 1
    y_top50 = top_50_users["Used"].sum()

    x_top100 = (cum_used >= top_100_users["Used"].sum()).idxmax() + 1
    y_top100 = top_100_users["Used"].sum()

    x_top200 = (cum_used >= top_200_users["Used"].sum()).idxmax() + 1
    y_top200 = top_200_users["Used"].sum()

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cum_used) + 1), cum_used)
    plt.title(f"Cumulative SUs Used by User (last {days} days)")
    plt.xlabel("Number of Users (ranked by usage)")
    plt.ylabel("Cumulative SUs Used")
    plt.grid(True)

    # horizontal line: from left edge (x=0) to the intersection point only
    plt.hlines(
        y=y_top1,
        xmin=0,
        xmax=x_top1,
        color="r",
        linestyle="--",
        label=f"Top User SUs: ({y_top1:,.0f}) ; {x_top1} users equivalent",
    )
    plt.hlines(
        y=y_top5,
        xmin=0,
        xmax=x_top5,
        color="g",
        linestyle="--",
        label=f"Top 5 Users SUs: ({y_top5:,.0f}) ; {x_top5} users equivalent",
    )
    plt.hlines(
        y=y_top10,
        xmin=0,
        xmax=x_top10,
        color="orange",
        linestyle="--",
        label=f"Top 10 Users SUs: ({y_top10:,.0f}) ; {x_top10} users equivalent",
    )
    plt.hlines(
        y=y_top25,
        xmin=0,
        xmax=x_top25,
        color="purple",
        linestyle="--",
        label=f"Top 25 Users SUs: ({y_top25:,.0f}) ; {x_top25} users equivalent",
    )
    plt.hlines(
        y=y_top50,
        xmin=0,
        xmax=x_top50,
        color="brown",
        linestyle="--",
        label=f"Top 50 Users SUs: ({y_top50:,.0f}) ; {x_top50} users equivalent",
    )
    plt.hlines(
        y=y_top100,
        xmin=0,
        xmax=x_top100,
        color="gray",
        linestyle="--",
        label=f"Top 100 Users SUs: ({y_top100:,.0f}) ; {x_top100} users equivalent",
    )
    plt.hlines(
        y=y_top200,
        xmin=0,
        xmax=x_top200,
        color="pink",
        linestyle="--",
        label=f"Top 200 Users SUs: ({y_top200:,.0f}) ; {x_top200} users equivalent",
    )
    plt.hlines(
        y=cum_used.iloc[-1],
        xmin=0,
        xmax=len(cum_used),
        color="b",
        linestyle="--",
        label=f"Total SUs: ({cum_used.iloc[-1]:,.0f}) ; {len(cum_used)} users total",
    )

    # vertical line: from bottom edge (y=0) to the intersection point only
    plt.vlines(x=x_top1, ymin=0, ymax=y_top1, color="r", linestyle="--")
    plt.vlines(x=x_top5, ymin=0, ymax=y_top5, color="g", linestyle="--")
    plt.vlines(x=x_top10, ymin=0, ymax=y_top10, color="orange", linestyle="--")
    plt.vlines(x=x_top25, ymin=0, ymax=y_top25, color="purple", linestyle="--")
    plt.vlines(x=x_top50, ymin=0, ymax=y_top50, color="brown", linestyle="--")
    plt.vlines(x=x_top100, ymin=0, ymax=y_top100, color="gray", linestyle="--")
    plt.vlines(x=x_top200, ymin=0, ymax=y_top200, color="pink", linestyle="--")

    plt.legend()
    plt.show()
