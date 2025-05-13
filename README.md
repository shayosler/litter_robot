# litter_robot
Scripts for working with the Whisker Litter Robot 4

# Automation
I set up a Google Cloud Run Job to run `update_weight_history.py` daily. Some notes since I'll probably forget what I did before I do this again

0. Create google cloud project ("Home Automation")
1. Enable sheets API
1. Create Docker registry to host container for the script (`home-automation`)
1. Push docker image (`update_pet_weights`) to registry
1. Create Service Account (`automaton`)
    1. IAM & Admin > Service Accounts > Create service account
    1. Grant service account roles to run Cloud Run Jobs and access Secrets
    1. Create a new key for the service account, download it
        1. Click on account > Keys > Add Key > JSON 
1. Share the spreadsheet to update with the Service Account
1. Create a secret to store the Litter Robot account password
1. Create Cloud Run Job to run the script
    1. Cloud Run > Deploy Container > Job
    1. Name `update-pet-weights` 
    1. Select the `update_pet_weights` image uploaded earlier
    1. Under "Container(s), Volumes, Connections, Security" > Container(s) > Variables & Secrets click "Reference a Secret", select the secret with the litter robot account password. Store it in the `LITTER_ROBOT_PASSWORD` env var
    1. Under "Container(s), Volumes, Connections, Security" > Container(s) set Task Timeout to 1 minute, retries to 0
    1. Under "Container(s), Volumes, Connections, Security" > Security select the `automaton` Service Account created earlier
    1. Create Job
1. Set up scheduling
    1. Cloud Run > Jobs > `update-pet-weights` > Triggers > Add Scheduler Trigger > set schedule to `0 7 * * *` to run at 0700 UTC (00:00 PDT) every day

