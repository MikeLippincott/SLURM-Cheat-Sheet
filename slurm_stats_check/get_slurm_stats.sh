#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=00:15:00
#SBATCH --partition=amilan
#SBATCH --qos=normal
#SBATCH --output=alpine_std_out_std_err-%j.out

# Load the slurm module
module purge
module load slurm
module load mambaforge

days=$1
USER=$2
n=25

# try to load env
mamba activate slurm_stats_env || mamba create -f environment.yaml
mamba activate slurm_stats_env

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/ notebooks/*.ipynb

# slurm_stats files
accounts_file="accounts_date_$%Y-%m-%d_%H:%M:%S.csv"
jobs_file="jobs_date_$%Y-%m-%d_%H:%M:%S.csv"



# Get the accounts and jobs data
suacct amc-general "$days" > $accounts_file
jobstats "$USER" "$days" > $jobs_file

# Run the python script
python slurm_stats.py --acct "$accounts_file" --jobs_stats "$jobs_file" --days "$days" --user "$USER" --top_n "n"
