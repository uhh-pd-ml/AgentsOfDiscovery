import os


def make_output_dir(basis_path, job_number: int = None):
    if not os.path.exists(basis_path):
        try:
            os.makedirs(basis_path)
        except FileExistsError:
            # Fallback for cases where the directory was created by another process
            pass
    
    start = 'run_'
    if job_number is not None:
        start = f'job_{job_number}_'
    # Create a unique subdirectory for this run
    # get the output folders
    folders = os.listdir(basis_path)
    # get the highest number
    highest_number = 0
    for folder in folders:
        if folder.startswith(start):
            try:
                number = int(folder.split("_")[-1])
                if number > highest_number:
                    highest_number = number
            except ValueError:
                pass
    # create the new folder
    i = highest_number + 1

    if basis_path[-1] != "/":
        basis_path += "/"

    run_dir = basis_path + start + str(i) + "/"
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
    
    return run_dir

