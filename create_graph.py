import json
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

#file_path="E:/OULU/Projects/sdmo_project_a/outputs/hive/metrics_hive_output.json"

def doPlot(file_path):
    folder_name = os.path.basename(os.path.dirname(file_path))
    # Load data for processing for analysis and visualization from the minned file
    with open(file_path,'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Extract required metrics
    refactor_commits = []
    for commit in data['commits_metrics']:
        refactor_commits.append(commit)

    # Initialize data structure for for analysis
    refactor_data = {
        'commit_number':[],
        'hash': [],
        'message': [],
        'EXP': [],
        'CEXP': [],
        'REXP': [],
        'NADEV': [],
        'NDDEV': [],
        'NF': [],
        'ADD': [],
        'DEL': [],
        'AGE':[],
        'ENTROPY': []
    }

    # load required data from the commit matrcs
    i=1
    for commit in refactor_commits:
        refactor_data['hash'].append(commit['refactor_hash'])
        refactor_data['message'].append(commit['refactor_msg'])
        refactor_data['EXP'].append(commit['general_metrics']['EXP'])
        refactor_data['CEXP'].append(commit['general_metrics']['CEXP'])
        refactor_data['REXP'].append(commit['general_metrics']['REXP'])
        refactor_data['NADEV'].append(commit['general_metrics']['NADEV'])
        refactor_data['NDDEV'].append(commit['general_metrics']['NDDEV'])
        refactor_data['NF'].append(commit['general_metrics']['NF'])
        refactor_data['commit_number'].append(i)
        i+=1
        
        # Aggregate ADD, DEL, and average ENTROPY of files in the each commit
        total_add, total_del, total_entropy,total_age = 0, 0, 0, 0
        for file_metric in commit['file_metrics']:
            total_add += file_metric['ADD']
            total_del += file_metric['DEL']
            total_entropy += file_metric['ENTROPY']
            total_age +=file_metric['AGE']
        
        refactor_data['ADD'].append(total_add)
        refactor_data['DEL'].append(total_del)
        refactor_data['ENTROPY'].append(total_entropy / len(commit['file_metrics']) if commit['file_metrics'] else 0)
        refactor_data['AGE'].append(total_age/len(commit['file_metrics']) if commit['file_metrics'] else 0)

    # Convert data to DataFrame for visualization
    df_refactor = pd.DataFrame(refactor_data)
    #df_refactor['commit_number'] = range(1, len(df_refactor) + 1)  # Add a sequential column for plotting

    # Plot selected metrics for analysis
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle("Evolution Across Refactoring Commits of Repository:"+folder_name)

    # Experience Metrics
    axes[0, 0].plot(df_refactor['commit_number'], df_refactor['EXP'], label='EXP')
    axes[0, 0].set_title("Developer Experience (EXP)")
    axes[0, 0].set_xlabel("Commit Number")
    axes[0, 0].set_ylabel("EXP")

    axes[0, 1].plot(df_refactor['commit_number'], df_refactor['CEXP'], label='CEXP')
    axes[0, 1].set_title("Cumulative Experience (CEXP)")
    axes[0, 1].set_xlabel("CCommit Number")
    axes[0, 1].set_ylabel("CEXP")

    # Number of Active Developers
    #axes[1, 0].plot(df_refactor['commit_number'], df_refactor['NADEV'], label='NADEV', marker='o',color='green')
    #axes[1, 0].set_title("Active Developers (NADEV)")
    #axes[1, 0].set_xlabel("Commit Number")
    #axes[1, 0].set_ylabel("NADEV")

    # Average AGE
    axes[1, 0].plot(df_refactor['commit_number'], df_refactor['AGE'], label='AGE',color='green')
    axes[1, 0].set_title("Average age of file modified (AGE)")
    axes[1, 0].set_xlabel("Commit Number")
    axes[1, 0].set_ylabel("AGE")

    #Number of files modified
    axes[1, 1].plot(df_refactor['commit_number'], df_refactor['NF'], label='NF', color='purple')
    axes[1, 1].set_title("Number of Files Modified (NF)")
    axes[1, 1].set_xlabel("Commit Number")
    axes[1, 1].set_ylabel("NF")

    # Additions, Deletions
    axes[2, 0].plot(df_refactor['commit_number'], df_refactor['ADD'], label='ADD', color='green')
    axes[2, 0].plot(df_refactor['commit_number'], df_refactor['DEL'], label='DEL', color='red')
    axes[2, 0].legend()
    axes[2, 0].set_title("Lines Added (ADD) and Deleted (DEL)")
    axes[2, 0].set_xlabel("Commit Number")
    axes[2, 0].set_ylabel("Lines")

    #commulative entropy
    axes[2, 1].plot(df_refactor['commit_number'], df_refactor['ENTROPY'], label='ENTROPY', color='orange')
    axes[2, 1].set_title("Change Entropy")
    axes[2, 1].set_xlabel("Commit Number")
    axes[2, 1].set_ylabel("Entropy")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
#    plt.show()
    plt.savefig("plot.png",dpi=300,bbox_inches='tight')

def main(output_file):
    # Check file exists
    if os.path.exists(output_file):
        #Plot graphs
        doPlot(output_file)
    else:
        print("File does not exists")     

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Use: python script.py <metrics_file_path>")
        sys.exit(1)

    f_path = sys.argv[1]
    main(f_path)