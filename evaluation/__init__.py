import os
from datetime import datetime

output_data_folder = "output_data"
root_folder = f"experiment_{datetime.today().strftime('%Y_%m_%d_%H_%M_%S')}"
experiment_root_path = os.path.join(output_data_folder, root_folder) 
experiment_log_path = os.path.join(experiment_root_path, "logs")

if not os.path.exists(os.path.join(output_data_folder)):
  os.makedirs(output_data_folder)


if not os.path.exists(experiment_root_path):
  os.makedirs(experiment_root_path)


if not os.path.exists(experiment_log_path):
  os.makedirs(experiment_log_path)


