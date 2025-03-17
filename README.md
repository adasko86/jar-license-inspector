# License Retrieval for JAR Libraries

An automatic script to retrieve licenses for JAR libraries from Maven Central Repository.

</br>
##✨ **Features**

Fetches license information based on groupId, artifactId, and version.

Checks multiple license sources:

Maven Central API – retrieves license metadata if available.

POM file (pom.xml) – parses the POM file to find the <licenses> section.

JAR file – checks LICENSE.txt and META-INF/MANIFEST.MF.

Generates a results table.


</br>
##📥 **Installation**

The script requires Python 3.x and a few libraries. Install them using:
```bash
pip install requests tabulate
```
or
```bash
pip3 install requests tabulate
```


</br>
##🚀 **Usage**

The script operates on a directory containing `.jar` files. To run it:

```bash
python JarLicenseInspector.py <path_to_jars_directory>
```

### **Example**:
```bash
python JarLicenseInspector.py ./libs
```


</br>
## 📋 **Results**
After execution, the script returns a table with results:

| JAR File                  | Artifact ID       | Version | License                    |
|---------------------------|-------------------|---------|----------------------------|
| commons-lang3-3.12.0.jar  | commons-lang3     | 3.12.0  | Apache License 2.0         |
| asm-9.7.1.jar            | asm               | 9.7.1   | BSD License                |
| no-license.jar           | no-license        | 1.0.0   | !!! No License Found !!!   |

Additionally, an **HTML report** will be generated, providing a detailed description of the licenses for each library. If the script does not find a license for a library, the table will display the value **"!!! No License Found !!!"**.

Furthermore, a dedicated **folder will be created**, where individual files containing the extracted licenses for each library will be stored.

![image](https://github.com/user-attachments/assets/05558d84-223c-4d59-8910-ac735a79abc0)



</br>
## 🛠 **How It Works?**

Finding groupId – if missing, retrieves from Maven Central.

Fetching license from Maven API – if available.

Parsing pom.xml – checks the <licenses> section.

Analyzing JAR file – searches for LICENSE and MANIFEST.MF.


</br>
##🔄 **Possible Enhancements**

Retrieve licenses using SPDX API.

Save results in CSV/JSON format.

Support GitHub/GitLab API for project repositories.


</br>
##👨‍💻 **Author**

Created by [adasko.86]. If you have any questions, feel free to open an issue! 😊
