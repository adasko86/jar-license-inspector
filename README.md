# License Retrieval for JAR Libraries

An automatic script to retrieve licenses for JAR libraries from Maven Central Repository.

</br>
✨ ### Features

Fetches license information based on groupId, artifactId, and version.

Checks multiple license sources:

Maven Central API – retrieves license metadata if available.

POM file (pom.xml) – parses the POM file to find the <licenses> section.

JAR file – checks LICENSE.txt and META-INF/MANIFEST.MF.

Generates a results table.


</br>
📥 ### Installation

The script requires Python 3.x and a few libraries. Install them using:

**pip install requests tabulate**


</br>
🚀 ### Usage

The script operates on a directory containing .jar files. To run it:

python get_license.py <path_to_directory>

Example:

python get_license.py ./libs


</br>
📋 ### Sample Output

After execution, the script returns a table with results:

| JAR File                  | Artifact ID       | Version | License                    |
|---------------------------|-------------------|---------|----------------------------|
| commons-lang3-3.12.0.jar  | commons-lang3     | 3.12.0  | Apache License 2.0         |
| asm-9.7.1.jar             | asm               | 9.7.1   | BSD License                |
| no-license.jar            | no-license        | 1.0.0   | License not found          |


</br>
🛠 ### How It Works?

Finding groupId – if missing, retrieves from Maven Central.

Fetching license from Maven API – if available.

Parsing pom.xml – checks the <licenses> section.

Analyzing JAR file – searches for LICENSE and MANIFEST.MF.


</br>
🔄 ### Possible Enhancements

Retrieve licenses using SPDX API.

Save results in CSV/JSON format.

Support GitHub/GitLab API for project repositories.


</br>
👨‍💻 ### Author

Created by [adasko.86]. If you have any questions, feel free to open an issue! 😊
