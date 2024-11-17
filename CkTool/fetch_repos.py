import pandas as pd
import os
from git import Repo
import time

def fetch_github_links_from_csv(file_path):
    """Fetch GitHub links from a CSV file."""
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(file_path)
    
    # Check if 'project_url' is a valid column, then extract the URLs
    if 'project_url' in df.columns:
        github_links = df['project_url'].tolist()
    else:
        print("Error: 'project_url' column not found in the CSV.")
        github_links = None
    
    return github_links

def fetch_and_clone_repositories(file_path, repos_folder="./cloned_repos/", max_retries=3):
    """Fetch and clone GitHub repositories from CSV links with retry logic."""
    github_links = fetch_github_links_from_csv(file_path)
    
    if not github_links:
        print("No GitHub links found.")
        return []    

    cloned_repos = []

    # Ensure the repos folder exists
    if not os.path.exists(repos_folder):
        os.makedirs(repos_folder)
    
    for link in github_links:
        # Extract the repo name from the URL
        repo_name = link.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(repos_folder, repo_name)
        
        # Check if the repo is already cloned (i.e., if the folder exists)
        if os.path.exists(repo_path):
            print(f"Repository {repo_name} already exists at {repo_path}. Skipping clone.")
            cloned_repos.append(repo_path)
        else:
            print(f"Cloning {repo_name} from {link}...")

            # Set the Git buffer size to avoid errors with large repos
            os.environ['GIT_HTTP_LOW_SPEED_LIMIT'] = '0'  # Disable speed limit
            os.environ['GIT_HTTP_LOW_SPEED_TIME'] = '999999'  # Allow longer time to fetch
            
            attempt = 0
            while attempt < max_retries:
                try:
                    # Clone the repository
                    Repo.clone_from(link, repo_path)
                    cloned_repos.append(repo_path)
                    break  # Exit the retry loop if successful
                except Exception as e:
                    print(f"Error cloning {repo_name}, attempt {attempt + 1}: {e}")
                    attempt += 1
                    if attempt < max_retries:
                        print(f"Retrying in 5 seconds...")
                        time.sleep(5)  # Wait before retrying
                    else:
                        print(f"Failed to clone {repo_name} after {max_retries} attempts.")
    
    return cloned_repos

