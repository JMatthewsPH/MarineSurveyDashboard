#!/bin/bash

METRICS=(
  "algae"
  "herbivore"
  "carnivore"
  "omnivore"
  "corallivore"
  "bleaching"
  "rubble"
)

for metric in "${METRICS[@]}"; do
  old_block="            if ${metric}_comparison == \"Compare with Sites\":
                compare_sites = [site for site in comparison_site_names if site != selected_site]
                ${metric}_compare_sites = st.multiselect(
                    \"Select sites to compare ${metric//\_/ }:\",
                    compare_sites,
                    key=\"${metric}_compare_sites\",
                    max_selections=5  # Limit to 5 sites for readability
                )"
  
  new_block="            if ${metric}_comparison == \"Compare with Sites\":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                # Define function to extract site names (filtering out headers)
                def extract_site_name(option):
                    if option.startswith(\"  \"):
                        return option.strip()
                    return None
                
                ${metric}_compare_sites = st.multiselect(
                    \"Select sites to compare ${metric//\_/ }:\",
                    options=comparison_options,
                    format_func=format_site_option,
                    key=\"${metric}_compare_sites\",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                ${metric}_compare_sites = [extract_site_name(site) for site in ${metric}_compare_sites if extract_site_name(site)]"
  
  # Escape special characters for sed
  old_block_escaped=$(echo "$old_block" | sed 's/\//\\\//g')
  new_block_escaped=$(echo "$new_block" | sed 's/\//\\\//g')
  
  # Perform the replacement
  sed -i "s/$old_block_escaped/$new_block_escaped/g" pages/Site_Dashboard.py
done
