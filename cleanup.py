import os
import shutil

finished_videos = ["chem_ch4", "stats 1"]

for raw_name in finished_videos:
    # Attempt to clean up all associated files and folders
    # base names:
    base_space = raw_name.replace('_', ' ')
    base_under = raw_name.replace(' ', '_')
    
    targets = [
        f"done {base_space}.m4a",
        f"done {base_under}.m4a",
        f"done {base_space}.m4a.txt",
        f"done {base_under}.m4a.txt",
        f"done {base_space}.json",
        f"done {base_under}.json",
        f"done {base_under}.m4a.json",
        f"done {base_space}.m4a.json"
    ]
    
    dirs = [
        base_space, # segmented audios folder
        base_under, # segmented audios folder alt
        f"done {base_space}_images",
        f"done {base_under}_images",
        f"done {base_space}.m4a_images",
        f"done {base_under}.m4a_images",
        f"done {base_under}", # the accidental one
        f"done {raw_name}"
    ]
    
    for f in targets:
        if os.path.exists(f) and os.path.isfile(f):
            try:
                os.remove(f)
                print(f"Deleted file: {f}")
            except Exception as e:
                print(f"Error deleting file {f}: {e}")
                
    for d in dirs:
        if os.path.exists(d) and os.path.isdir(d):
            try:
                shutil.rmtree(d)
                print(f"Deleted directory: {d}")
            except Exception as e:
                print(f"Error deleting directory {d}: {e}")
