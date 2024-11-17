import subprocess
import os
import json
import shutil
from git import Repo
from pathlib import Path
from fetch_repos import fetch_and_clone_repositories  # Import the new function to fetch repos


# Paths to CK jar and where to store repositories and outputs
ck_jar_path = "ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"
repos_folder = "./cloned_repos/"
output_data_folder = "./saved_metrics_data/"  # Folder to save JSON output metrics

# Path to track failed or skipped repositories
failed_repos_file = "failed_repos.json"  # This will store the URLs of failed repositories

# Create necessary folders if they don’t exist
Path(repos_folder).mkdir(parents=True, exist_ok=True)
Path(output_data_folder).mkdir(parents=True, exist_ok=True)

# the repos that are not consisent with .jar dependencies will not be analyzed and moved to failed_repos.json
def log_failed_repo(repo_url, reason):
    """Logs the failed or skipped repository URL and the reason."""
    failed_repos = []
    
    if os.path.exists(failed_repos_file):
        with open(failed_repos_file, "r") as f:
            failed_repos = json.load(f)

    failed_repos.append({"repo_url": repo_url, "reason": reason})
    
    with open(failed_repos_file, "w") as f:
        json.dump(failed_repos, f, indent=4)

def clone_repository(git_url):
    """Clones the GitHub repository to clone_repos_folder and returns the local path."""
    repo_name = git_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(repos_folder, repo_name)
    if not os.path.exists(repo_path):
        print(f"Cloning {repo_name}...")
        try:
            Repo.clone_from(git_url, repo_path)
        except Exception as e:
            print(f"Error cloning {repo_name}: {e}")
            log_failed_repo(git_url, str(e))  # Log the failure
            return None
    else:
        print(f"{repo_name} already cloned.")
    return repo_path

# analysis of class and method metrics
def run_ck_analysis(repo_path):
    """Runs CK on the cloned repository and saves output as separate CSV files."""
    try:
        print(f"Running CK analysis on {repo_path}...")
        # command = [
        #     "java", "-jar", ck_jar_path, repo_path, "false", "0", "false", output_data_folder
        # ]
        command = [
            "java", "-Xmx2g", "-jar", ck_jar_path, repo_path, "false", "0", "false", output_data_folder]

        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        # Print CK's standard output and error for debugging
        print("CK Output:\n", result.stdout)
        print("CK Errors:\n", result.stderr)

        # Now check if the output files exist in output_data_folder
        class_metrics_file = os.path.join(output_data_folder, "class.csv")
        method_metrics_file = os.path.join(output_data_folder, "method.csv")
        
        # Create lists to hold class and method metrics
        class_metrics_data = []
        method_metrics_data = []

        # Read class-level metrics into JSON
        if os.path.exists(class_metrics_file):
            with open(class_metrics_file, "r") as f:
                headers = f.readline().strip().split(",")
                for line in f:
                    values = line.strip().split(",")
                    class_metrics = dict(zip(headers, values))
                    class_metrics_data.append(class_metrics)
        
        # Read method-level metrics into JSON
        if os.path.exists(method_metrics_file):
            with open(method_metrics_file, "r") as f:
                headers = f.readline().strip().split(",")
                for line in f:
                    values = line.strip().split(",")
                    method_metrics = dict(zip(headers, values))
                    method_metrics_data.append(method_metrics)
        
        # Create a unique output folder for each repository (under their repo name)
        repo_name = os.path.basename(repo_path)
        repo_output_folder = os.path.join(output_data_folder, repo_name)
        Path(repo_output_folder).mkdir(parents=True, exist_ok=True)

        # Save class metrics to a JSON file
        class_metrics_json_file = os.path.join(repo_output_folder, f'{repo_name}_class_metrics.json')
        with open(class_metrics_json_file, "w") as json_file:
            json.dump(class_metrics_data, json_file, indent=4)
        print(f"Class metrics saved to {class_metrics_json_file}")

        # Save method metrics to a JSON file
        method_metrics_json_file = os.path.join(repo_output_folder, f'{repo_name}_method_metrics.json')
        with open(method_metrics_json_file, "w") as json_file:
            json.dump(method_metrics_data, json_file, indent=4)
        print(f"Method metrics saved to {method_metrics_json_file}")


        if os.path.exists(class_metrics_file):
            os.remove(class_metrics_file)
            print(f"Deleted {class_metrics_file}")

        if os.path.exists(method_metrics_file):
            os.remove(method_metrics_file)
            print(f"Deleted {method_metrics_file}")

    except subprocess.CalledProcessError as e:
        print(f"CK analysis failed for {repo_path}: {e}")
        log_failed_repo(repo_path, str(e))  # Log the failure

# delete the repo after analysis
def clean_up(repo_path):
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
        print(f"Deleted repository at {repo_path} to save space.")

def fetch_and_analyze_repos(file_path):
    """Fetches repositories using fetch_repos.py and analyzes them."""
    print("Fetching and cloning repositories...")
    cloned_repos = fetch_and_clone_repositories(file_path)  # Pass file_path for the CSV
    if not cloned_repos:
        print("No repositories to analyze.")
        return

    for repo_url in cloned_repos:
        print(f"Analyzing repository: {repo_url}")
        repo_path = clone_repository(repo_url)
        
        # If cloning failed, skip further analysis for this repo
        if not repo_path:
            print(f"Skipping analysis for {repo_url} due to cloning error.")
            continue

        run_ck_analysis(repo_path)
        clean_up(repo_path)

def main():
    """Main function to initiate the fetch and analyze process."""
    # CSV file to automatically pick the github repo url one by one for cloning and analysis
    file_path = "ProjectGithubLinks.csv"  
    fetch_and_analyze_repos(file_path)
    

if __name__ == "__main__":
    main()
