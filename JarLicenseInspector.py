import requests
import xml.etree.ElementTree as ET
import re
import sys
import zipfile
import io
import os
from tabulate import tabulate
from time import sleep
from datetime import datetime

def make_request_with_retries(url, retries=3, timeout=10):
    """Makes an HTTP request with multiple attempts to minimize connection problems."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Checks if the response was correct (status 200)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error while retrieving {url}: {e}. Attemp {attempt + 1}/{retries}.")
            if attempt < retries - 1:
                sleep(2)  # Wait 2 seconds before trying again
            else:
                print(f"Nie udało się pobrać {url} po {retries} próbach.")
                return None

def get_group_id(artifact_id, version):
    """Gets the groupId for the given artifactId and version from the Maven Central API."""
    search_url = f"https://search.maven.org/solrsearch/select?q=a:{artifact_id}+AND+v:{version}&rows=1&wt=json"
    response = make_request_with_retries(search_url)
    if not response:
        return None
    
    data = response.json()
    docs = data.get("response", {}).get("docs", [])
    return docs[0].get("g") if docs else None

def is_valid_url(url):
    """Regular expression to check URL"""
    regex = re.compile(
        r'^(?:http|ftp)s?://' # check http://, https://, ftp://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # sprawdza domenę
        r'localhost|' # or localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # or IP
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # or adres IPv6
        r'(?::\d+)?' # port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(regex, url) is not None

def get_license_from_pom(group_id, artifact_id, version):
    """Gets the license from the pom.xml file."""
    if not group_id:
        return None
    
    group_path = group_id.replace(".", "/")
    pom_url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    response = make_request_with_retries(pom_url)
    if not response:
        return None
    
    # Remove the namespace from XML
    xml_data_without_namespace = re.sub(r'\{.*?\}', '', response.text)
    
    root = ET.fromstring(xml_data_without_namespace.replace('xmlns="http://maven.apache.org/POM/4.0.0"',""))
    licenses = root.findall(".//licenses/license/name")
    
    licensesURL = root.find(".//licenses/license/url")
    if licensesURL is not None:
        try_get_licence_from_url_and_save_to_file(artifact_id, licensesURL.text)
    
    return [lic.text for lic in licenses] if licenses else None

def try_get_licence_from_url_and_save_to_file(artifact_id, licensesURL):
    """Try to download the license from url and save it to file."""
    if licensesURL is not None:
        if is_valid_url(licensesURL):
            responseLicence = make_request_with_retries(licensesURL)   
            if responseLicence is not None:
                if responseLicence.status_code == 200:  # Check if the response is correct
                    save_license_to_file(artifact_id, responseLicence.text)

def save_license_to_file(artifactId, content):
    """Trying to save license to file."""
    
    # Path to the folder where you want to save the file
    folder_path = 'licenses'

    # Checking if the folder exists, if not, we create it
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Path to the file we want to save in this folder
    file_path = os.path.join(folder_path, f'{artifactId}.licence')

    # Getting the current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Opening a file in write mode
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(f'{content}\n\n')
        # Adding file creation date
        file.write(f"Generated: {current_datetime}\n")

    print(f"File was written in: {file_path}")

def get_license_from_jar(group_id, artifact_id, version):
    """Gets the license from the JAR file (by looking in LICENSE.txt and META-INF/MANIFEST.MF)."""
    if not group_id:
        return None

    group_path = group_id.replace(".", "/")
    jar_url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.jar"
    response = make_request_with_retries(jar_url)
    if not response:
        return None

    with zipfile.ZipFile(io.BytesIO(response.content), 'r') as jar:
        # We are looking for license files
        for file_name in jar.namelist():
            if "LICENSE" in file_name.upper():
                with jar.open(file_name) as f:
                    license_content = f.read().decode(errors="ignore")                        
                    save_license_to_file(f'{artifact_id}-{version}', license_content)                
                    return [extract_license_from_license_file(license_content)]
        
        # Checking META-INF/MANIFEST.MF
        if "META-INF/MANIFEST.MF" in jar.namelist():
            with jar.open("META-INF/MANIFEST.MF") as f:
                manifest_content = f.read().decode(errors="ignore")
                license_info = extract_license_from_manifest(manifest_content) 
                                           
                if license_info is not None and len(license_info) >= 2:
                    try_get_licence_from_url_and_save_to_file(artifact_id, license_info[1])    
                    
                return [" ".join(license_info)] if license_info else ["!!! No Licence Found !!!"]
    
    return None

def extract_license_from_license_file(content):
    """Trying to recognize the license in the file LICENSE.txt."""
    license_match = re.search(r'(^.*License)(:?\s*.*)', content, re.MULTILINE)
    return license_match.group(1).strip() + " " + license_match.group(2).strip() if license_match else "!!! No Licence Found !!!"

def extract_license_from_manifest(content):
    """Trying to recognize the license in the MANIFEST.MF file."""
    license_match = re.search(r'(.*License):(\s*.*)', content, re.MULTILINE)
    return [license_match.group(1).strip(), license_match.group(2).strip()] if license_match else None

def extract_artifact_and_version(filename):
    """Extracts artifactId and version from JAR filename."""
    match = re.match(r"(.+)-(\d+\.\d+(\.\d+)?(-[\w\d]+)?)\.jar$", filename)
    return (match.group(1), match.group(2)) if match else (None, None)

def process_jar_files_in_directory(directory):
    """Processes all .jar files in the directory and generates a table with licenses."""
    result = []
    
    # Go through all the files in the directory
    for filename in os.listdir(directory):
        licence_was_found_and_print = False
        if filename.endswith(".jar"):
            jar_path = os.path.join(directory, filename)
            artifact_id, version = extract_artifact_and_version(filename)

            if artifact_id and version:
                print(f"Checking {artifact_id}-{version}:", end=" ")
                group_id = get_group_id(artifact_id, version)                
               
                # 1⃣ Check the POM file
                licenses = get_license_from_pom(group_id, artifact_id, version)
                
                # 2⃣ If still not there, check JAR
                if not licenses:
                    licenses = get_license_from_jar(group_id, artifact_id, version)
                elif licenses and not licence_was_found_and_print: 
                    licence_was_found_and_print = True                 
                    print("Licence Found in POM")

                # 3⃣ If we didn't find anything, we return no license
                if not licenses:
                    licenses = ["!!! No Licence Found !!!"]
                    print("No Licence Found!!!")
                elif licenses and not licence_was_found_and_print:
                    licence_was_found_and_print = True
                    print("Licence Found in JAR")

                # Add the result to the table
                result.append([filename, artifact_id, version, ", ".join(licenses)])

    return result

def generate_html_table(data):
    """Generate HTML table."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Licenses JAR</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
            h2 { text-align: center; }
            table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #0073e6; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <h2>Licenses</h2>
        <table>
            <tr>
                <th>JAR file</th>
                <th>Artifact ID</th>
                <th>Version</th>
                <th>License</th>
            </tr>
    """
    for row in data:
        html += f"""
            <tr>
                <td>{row[0]}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td>{row[3]}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usuage: python script.py <path to folder with jars>")
        sys.exit(1)

    directory = sys.argv[1]

    # Check if the given directory exists
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a folder.")
        sys.exit(1)

    # Process all JAR files in the directory
    result = process_jar_files_in_directory(directory)

    # 📋 Generate a table of results
    if result:
        # Save to file
        html_content = generate_html_table(result)
        output_file = "license.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"HTML table save in: {output_file}")
        print(tabulate(result, headers=["JAR file", "Artifact ID", "Version", "License"], tablefmt="grid"))
    else:
        print("No JAR files found in the specified directory.")
