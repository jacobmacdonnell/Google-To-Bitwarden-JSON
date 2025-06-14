import csv
import json
import argparse
import sys

def convert_google_to_bitwarden(input_csv_path, output_json_path):
    """
    Reads a Google Passwords CSV, groups entries by the 'name' field,
    and converts them to a Bitwarden JSON format, consolidating multiple URLs
    under a single login item.
    """
    print(f"Reading Google Passwords CSV from: {input_csv_path}")

    # This dictionary will store the consolidated login items.
    # The key will be the 'name' from the Google CSV (e.g., "Google", "Amazon.com").
    # The value will be the fully formed Bitwarden item.
    grouped_items = {}

    try:
        with open(input_csv_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            
            # Verify that the CSV has the expected Google headers
            expected_headers = ['name', 'url', 'username', 'password']
            if not all(h in reader.fieldnames for h in expected_headers):
                print("\n[ERROR] The CSV file does not have the correct Google Passwords format.")
                print(f"--> Expected headers to include: {expected_headers}")
                print(f"--> Found headers: {reader.fieldnames}")
                sys.exit(1)

            for row in reader:
                # Extract data from the current row
                name = row.get('name')
                url = row.get('url')
                username = row.get('username')
                password = row.get('password')
                note = row.get('note', '') # Use .get() for the optional 'note' field

                # Skip invalid rows that are missing essential information
                if not name or not url or not username:
                    continue

                # --- This is the core logic ---
                # If we have NOT seen this 'name' before, create a new Bitwarden item
                if name not in grouped_items:
                    grouped_items[name] = {
                        "type": 1,  # 1 is the type for a "login" item in Bitwarden
                        "name": name,
                        "notes": note if note else None,
                        "favorite": False,
                        "login": {
                            "uris": [{"uri": url, "match": None}], # Start a list of URLs
                            "username": username,
                            "password": password,
                            "totp": None
                        },
                        "fields": []
                    }
                # If we HAVE seen this 'name' before, just add the new URL to the existing item
                else:
                    existing_item = grouped_items[name]
                    existing_item['login']['uris'].append({"uri": url, "match": None})
                    
                    # --- Conflict Handling ---
                    # Warn the user if a different username/password is found for the same site name.
                    # The script will keep the *first* set of credentials it found.
                    if (existing_item['login']['username'] != username or 
                        existing_item['login']['password'] != password):
                        
                        print(f"  [WARNING] Conflicting credentials found for '{name}'.")
                        print(f"    - URL '{url}' has a different username/password.")
                        print(f"    - Sticking with the first credentials found for this name.")
                        
                        # Optionally, add the conflicting info to the notes for manual review
                        conflict_note = (
                            f"\n\n--- AUTO-MERGE WARNING ---\n"
                            f"An entry for the URL below had different credentials and was not merged automatically:\n"
                            f"URL: {url}\n"
                            f"Username: {username}\n"
                        )
                        if existing_item['notes']:
                            existing_item['notes'] += conflict_note
                        else:
                            existing_item['notes'] = conflict_note.strip()


    except FileNotFoundError:
        print(f"\n[ERROR] The file '{input_csv_path}' was not found. Please check the path.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)

    # Prepare the final JSON structure required by Bitwarden
    bitwarden_output = {
        "encrypted": False,
        "folders": [],
        "items": list(grouped_items.values()) # We only need the items, not the keys we used for grouping
    }

    # Write the formatted JSON to the output file
    try:
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(bitwarden_output, json_file, indent=2) # indent=2 makes the file readable
        print("\n----------------------------------------------------")
        print("✅ Success! Your Bitwarden import file is ready.")
        print(f"   - Processed {len(grouped_items)} unique login items.")
        print(f"   - File created at: {output_json_path}")
        print("----------------------------------------------------\n")
    except Exception as e:
        print(f"[ERROR] Could not write the output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Setup a user-friendly command-line interface
    parser = argparse.ArgumentParser(
        description="Consolidates a Google Passwords CSV into a Bitwarden-compatible JSON file.",
        epilog="Example: python google_to_bitwarden_converter.py 'Google Passwords.csv' bitwarden_import.json"
    )
    parser.add_argument(
        "input_csv",
        help="Path to your input 'Google Passwords.csv' file."
    )
    parser.add_argument(
        "output_json",
        help="Path for the output 'bitwarden_import.json' file."
    )
    
    args = parser.parse_args()
    convert_google_to_bitwarden(args.input_csv, args.output_json)
