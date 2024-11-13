# GitHub Repository Analysis: Refactoring Detection and Metrics Extraction

## Description

This project allows cloning a GitHub repository, analyzing its refactorings using [RefactoringMiner](https://github.com/tsantalis/RefactoringMiner), filtering commits with refactorings, and calculating various metrics from the repository's commit history.

## Features

- **Repository Cloning**: Clone a specified GitHub repository locally.
- **Refactoring Detection**: Use RefactoringMiner to detect refactorings in the commits.
- **Commit Filtering**: Filter commits that include refactorings.
- **Metrics Generation**: Calculate various commit metrics, such as the number of modified files, added/deleted lines, involved developers, and more.
- **Repository Cleanup**: Deletes the cloned repository after processing to free up local space.

## Prerequisities
- **Python 3.8+**
- **Javalang** 
- **Pydriller** 
- **Git**

## Usage

To run the script you use the following command line

```bash
python script.py <github_url>
```