# https://github.com/bennidi/mbassador.git
import os
import subprocess
import sys
import math
import json
import shutil
import re
import javalang
from datetime import timedelta
from typing import *
from pydriller import *
from classes import *

def clone_repo(github_url, repos_dir):
    try:
        repo_name = github_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join(repos_dir, repo_name)

        if os.path.exists(repo_path):
            print(f"The repository {repo_name} already exists in:  {repo_path}. Skipping clonning.")
            return repo_path
        
        subprocess.run(['git', 'clone', github_url, repo_path], check=True)
        return repo_path
    except subprocess.CalledProcessError as e:
        print(f"Error at clonning the repository: {e}")
        sys.exit(1)

def run_refactoring_miner(repo_path, output_dir):
    repo_name = os.path.basename(repo_path)

    repo_output_dir = os.path.join(output_dir, repo_name)
    os.makedirs(repo_output_dir, exist_ok=True)

    name_file = f'outputs/{repo_name}/{repo_name}_output.json'
    json_output_path = os.path.join(repo_output_dir, f'{repo_name}_output.json')

    if os.path.exists(json_output_path):
        print(f"RefactoringMiner output already exists at: {json_output_path}")
        return json_output_path

    refactoring_miner_path = r'.\RefactoringMiner-3.0.9\bin\RefactoringMiner'

    test = os.path.normpath(name_file)

    command = f'{refactoring_miner_path} -a {repo_path} -json "{test}"'
    try:
        subprocess.run(command,check=True, shell=True)
        print(f"Output saved in: {json_output_path}")
        return json_output_path
    except subprocess.CalledProcessError as e:
        print(f"Error RefactoringMiner: {e}\n")
        sys.exit(1)

def filter_commits_with_refactorings(input_json_path):
    try:
        # Generate output path by adding 'filtered_' prefix to the original file name
        dir_name = os.path.dirname(input_json_path)
        base_name = os.path.basename(input_json_path)
        output_json_path = os.path.join(dir_name, f'filtered_{base_name}')

        with open(input_json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        commits_with_refactorings = [commit for commit in data['commits'] if commit['refactorings']]
        
        filtered_data = {
            "commits": commits_with_refactorings
        }

        # Save the filtered JSON to a new file
        with open(output_json_path, 'w', encoding='utf-8') as output_file:
            json.dump(filtered_data, output_file, indent=4, ensure_ascii=False)

        print(f"Filtered commits saved to {output_json_path}")
        return commits_with_refactorings

    except Exception as e:
        print(f"Error processing the JSON file: {e}")

def save_commit_messages(dict_commit, repo_path, json_path):
    dir_name = os.path.dirname(json_path)
    base_name = os.path.basename(json_path)
    output_json_path = os.path.join(dir_name, f'ordered_msg_{base_name}')

    '''
    if os.path.exists(output_json_path):
        print(f"Ordered commit messages already exist at: {output_json_path}")
        return output_json_path
    '''
    ref_commits = set()
    total_commits = set()
    relevant_hashes = set(commit['sha1'] for commit in dict_commit)

    for c in Repository(repo_path).traverse_commits():
        value = c.hash in relevant_hashes
        n_commit = F_Commit(c.hash,
                            c.msg, 
                            c.author_date, 
                            c.author.name, # Check if necesary to save both.
                            c.committer.name,
                            c.lines,
                            c.files, 
                            value, 
                            c.parents[0] if c.parents else None)
        
        commit_files = set()
        for f in c.modified_files:
            f_file = F_File(f.filename, f.new_path, f.old_path ,f.diff, f.added_lines,f.nloc ,f.deleted_lines)
            
            if f.filename.endswith('.java') and f.new_path != None:
                file_path = os.path.join(repo_path, f.new_path)
                normalized_path = os.path.normpath(file_path)
                package_name = get_java_details(normalized_path)
                if package_name != None:
                    f_file.add_package(package_name)
            
            commit_files.add(f_file)

        n_commit.add_Files(commit_files)
        total_commits.add(n_commit)

        if value:
            ref_commits.add(n_commit)

    ref_commits = sorted(ref_commits, key=lambda c: c.date)
    total_commits = sorted(total_commits, key=lambda c: c.date)
    
    commits_serializable = [c.to_dict() for c in ref_commits]

    with open(output_json_path, 'w', encoding='utf-8') as output_file:
        json.dump(commits_serializable, output_file, indent=4, ensure_ascii=False)

    print(f"Ordered commits saved to {output_json_path}")
    return ref_commits, total_commits

def get_java_details(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            java_code = file.read()

        tree = javalang.parse.parse(java_code)
        
        package_name = tree.package

        if package_name:
            return package_name.name
        else:
            return None

    except FileNotFoundError:
        return None
    except Exception as e:
        return None

def get_metrics(tot_commits, ref_commits, json_path):
    dir_name = os.path.dirname(json_path)
    base_name = os.path.basename(json_path)
    output_json_path = os.path.join(dir_name, f'metrics_{base_name}')

    pattern = r'(Fix\w*|BugFix\w*|Bug\w*|Solv\w*)\s+#\d+'

    commits_list = set()
    i = 0
    for c in ref_commits:
        current_commit: Commit_Metric = Commit_Metric(c.hash, c.date, c.msg)
        files_per_commit: Set[File_Metric] = set()
        g_metric = General_Metric()
        g_metric.nf = c.total_files
        directory_list = set()
        packages_list = set()

        old_rute = []
        new_rute = []

        if re.search(pattern, c.msg,  re.IGNORECASE):
            g_metric.fix = True

        for ref_file in c.files:
            if ref_file.pkg_name is not None:
                packages_list.add(ref_file.pkg_name)

            if ref_file.old_filepath:
                old_rute = ref_file.old_filepath.split(os.sep)
                directory_list.update(old_rute[:-1])

            if ref_file.new_filepath:
                new_rute = ref_file.new_filepath.split(os.sep)
                directory_list.update(new_rute[:-1])
            
            m_file = File_Metric(ref_file.name, ref_file.old_filepath, ref_file.new_filepath, ref_file.pkg_name)        
            if c.total_lines > 0:
                m_file.entropy = round((ref_file.added_lines + ref_file.deleted_lines) / c.total_lines, 2)
            files_per_commit.add(m_file)
        
        g_metric.nd = len(directory_list)
        g_metric.ns = len(packages_list)
        # For metric by metric
        file_names_in_commit = {file.name for file in files_per_commit}
        for x in range(i, len(tot_commits)):
            if c.hash == tot_commits[x].hash:
                i = x
                break

            files_dict = {file.name: file for file in tot_commits[x].files}

            if file_names_in_commit.issubset(files_dict):
                g_metric.ncomm += 1
                g_metric.ammount_adevs.add(tot_commits[x].author)
            
            for file in files_per_commit:
                if file.name in files_dict:
                    file.add_adev(tot_commits[x].author)
                    file.increase_comm()

        g_metric.nadev = len(g_metric.ammount_adevs)

        total_lines_by_dev = {}
        total_commits_by_commiter = {}
        total_dates_by_commiter = {}

        # For init to current metric
        for x in range(len(tot_commits)):
            files_dict = {file.name: file for file in tot_commits[x].files}

            commiter = tot_commits[x].commiter
            author = tot_commits[x].author
            total_commits_by_commiter[commiter] = total_commits_by_commiter.get(commiter, 0) + 1
            total_dates_by_commiter.setdefault(commiter, []).append(tot_commits[x].date)
            total_lines_by_dev[author] = total_lines_by_dev.get(author, 0) + tot_commits[x].total_lines

            if file_names_in_commit.issubset(files_dict):
                g_metric.ammount_ddevs.add(tot_commits[x].author)

            for file in files_per_commit:
                if c.author == tot_commits[x].author and file.pkg_name != None:
                    for f_x in tot_commits[x].files:
                        if f_x.pkg_name == file.pkg_name:
                            file.sexp += 1
                            
                if file.name in files_dict:
                    modified_file: ModifiedFile = files_dict[file.name]
                    file.dates.append(tot_commits[x].date)
                    
                    if len(file.days) == 0:
                        file.days.append(0)
                    else:
                        tmp = len(file.dates)
                        days_in_btw = file.dates[tmp-1] - file.dates[tmp-2]
                        file.days.append(days_in_btw.days)

                    added_lines = modified_file.added_lines
                    deleted_lines = modified_file.deleted_lines
                    file.add_ddev(tot_commits[x].author)
                    file.calc_lines(added_lines, deleted_lines, tot_commits[x].author)
                    file.get_minor()

                    file.oexp = round(total_lines_by_dev[file.high_contributer] / sum(total_lines_by_dev.values()),2)
                    file.nuc += 1
                    if c.hash != tot_commits[x].hash:
                        file.lt = files_dict[file.name].nloc

            if c.hash == tot_commits[x].hash:
                break
        
        values = list(total_lines_by_dev.values())

        log_sum = sum(math.log(value) for value in values if value > 0)
        g_metric.exp = round(math.exp(log_sum / len(values)), 2)
        
        g_metric.nddev = len(g_metric.ammount_adevs)
        g_metric.cexp = total_commits_by_commiter[c.commiter]

        dates = total_dates_by_commiter[c.commiter]
        total_dates  = max(dates)
        one_month_ago = total_dates  - timedelta(days=30)
        last_month_dates = [d for d in dates if d >= one_month_ago]
        g_metric.rexp = len(last_month_dates)

        files_per_commit = sorted(files_per_commit, key=lambda c:c.name.lower())

        for file in files_per_commit:
            file.age = round(sum(file.days) / len(file.days), 2)

        current_commit.add_metrics(files_per_commit)
        current_commit.general_metric = g_metric
        commits_list.add(current_commit)
        

    commits_list = sorted(commits_list, key=lambda c: c.date)

    commits_dict = {
        "commits_metrics": [
            {
                "refactor_hash": commit.commit_hash,
                "refactor_msg": commit.msg,
                "file_metrics": commit.file_metrics,
                "general_metrics": commit.general_metric.to_dict()  # Assuming file_metrics is already structured as needed
            }
            for commit in commits_list
        ]
    }

    with open(output_json_path, 'w', encoding='utf-8') as output_file:
        json.dump(commits_dict, output_file, indent=4, ensure_ascii=False)

    print(f"Commits Metrics saved to {output_json_path}")

def delete_repo(repo_path):
    if os.path.exists(repo_path):
        try:
            # Attempt to remove the repository directory
            shutil.rmtree(repo_path)
            print(f"Deleted repository at: {repo_path}")
        except Exception as e:
            print(f"Error deleting repository: {e}")
            print("Attempting to delete files individually...")
            for root, dirs, files in os.walk(repo_path, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        os.remove(file_path)
                        print(f"Deleted file: {file_path}")
                    except PermissionError:
                        print(f"Permission denied for file: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete file {file_path}: {e}")

                # Now try to remove the directories
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        os.rmdir(dir_path)
                        print(f"Deleted directory: {dir_path}")
                    except OSError:
                        print(f"Could not delete directory {dir_path} (might not be empty or permission issue).")

            # Finally, try to delete the main repository directory again
            try:
                shutil.rmtree(repo_path)
                print(f"Successfully deleted repository at: {repo_path}")
            except Exception as e:
                print(f"Failed to delete repository after attempting individual file deletions: {e}")
    else:
        print(f"Repository path does not exist: {repo_path}")


def main(github_url):
    # Change this to local path
    root_dir = os.getcwd()
    repos_dir = os.path.join(root_dir, 'repos')
    outputs_dir = os.path.join(root_dir, 'outputs')

    # Verify if I can make this general without absolute path
    os.makedirs(repos_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)

    repo_path = clone_repo(github_url, repos_dir)

    json_path = run_refactoring_miner(repo_path, outputs_dir)

    ref_commits = filter_commits_with_refactorings(json_path)

    ref_commits, tot_commits = save_commit_messages(ref_commits, repo_path, json_path)

    get_metrics(tot_commits, ref_commits, json_path)

    delete_repo(repo_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Use: python script.py <github_url>")
        sys.exit(1)

    github_url = sys.argv[1]
    main(github_url)
