#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=06:00:00
#SBATCH --partition=amilan
#SBATCH --qos=normal
#SBATCH --output=alpine_std_out_std_err-%j.out

# Load the slurm module
module purge
module load slurmtools
module load mambaforge
module load anaconda

conda init bash

days=30
USER="$USER"
n=25

# load env
conda activate slurm_stats_env

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/ notebooks/*.ipynb

# stats files dir
slurm_stats_files_dir="slurm_stats_files"
# make the dir if it does not exist
mkdir -p "$slurm_stats_files_dir"
cd $slurm_stats_file_dir

accounts_file="$(date +%Y-%m-%d_%H:%M:%S)_accounts_date.csv"
jobs_file="$(date +%Y-%m-%d_%H:%M:%S)_jobs_date.csv"

# Get the accounts and jobs data
suacct amc-general "$days" > "$accounts_file"
jobstats "$USER" "$days" > "$jobs_file"

cd ../scripts

# Run the python script
python slurm_stats.py --acct "$accounts_file" --jobs_stats "$jobs_file" --days "$days" --user "$USER" --top_n "$n"

