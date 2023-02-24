# Command update-packages
## Usage
```bash
# Does not make updates runs apt update with --dry-run flag
juju-spell update-packages --patch ./updates.yaml --dry-run

# Makes the updates according to provided inputs
juju-spell update-packages --patch ./updates.yaml --dry-run
```
## Help Page
```bash
$>juju-spell update-packages --help
Usage:
    juju-spell update-packages [options]

Summary:
    This command will patch the cve by updating certain components.

    ---
    applications:
    - application: "^.*ubuntu.*$"
      dist_upgrade: True
      packages_to_update:
      - app: nova-common
        version: 2:21.2.4-0ubuntu2.1
      - app: python3-nova
        version: 2:21.2.4-0ubuntu2.1
    - application: "^.*nova-cloud-controller.*$"
      dist_upgrade: False
      packages_to_update:
      - app: nova-common
        version: 2:21.2.4-0ubuntu2.1
      - app: python3-nova
        version: 2:21.2.4-0ubuntu2.1

    Example:
    $ juju_spell update-packages --patch patchfile.yaml

Options:
       -h, --help:  Show this help message and exit
    -v, --verbose:  Show debug information and be more verbose
      -q, --quiet:  Only show warnings and errors, not progress
      --verbosity:  Set the verbosity level to 'quiet', 'brief',
                    'verbose', 'debug' or 'trace'
        --version:  Show the application version and exit
     -c, --config:  Set the path to custom config.
        --dry-run:  This will only run pre-check and dry-run only
                    instead of real execution.
     --no-confirm:  This will skip all the confirm check.
       --run-type:  parallel, batch or serial
         --filter:  Key-value pair comma separated string in double
                    quotes e.g., "a=1,2,3 b=4,5,6".
         --models:  model filter
         --patch:   patch file

See also:
    add-user
    enable-user
    grant
    remove-user

For a summary of all commands, run 'juju-spell help --all'.
```

## Parametres
**--patch**: location of patch file
[sample](update_packages-input.yaml)
```yaml
applications:
- application: "^.*ubuntu.*$" # [1]
  dist_upgrade: True # [2]
  packages_to_update:
  - app: nova-common # [3]
    version: 2:21.2.4-0ubuntu2.1 # [4]
  - app: python3-nova
    version: 2:21.2.4-0ubuntu2.1
- application: "^.*nova-cloud-controller.*$"
```

* **[1]** regular expression for applications to match
* **[2]** if true juju-spell does not updates specific packages, updates all the packages
* **[3]** apt package name to update
* **[4]** package version to match

## Result
[sample](update_packages-retval.json)

```json
[
 {
  "context": { ... },
  "success": true,
  "output": {
   "model1": {
    "applications": [
     { // [1],
      "name_expr": "^.*ubuntu.*$",
      "results": [] // [2]
     },
     { // [1]
      "name_expr": "^.*nova-cloud-controller.*$",
      "results": [ // [3]
       {
        "units": [ // [4]
         {
          "unit": "nova-cloud-controller/0", // [5]
          "command": "sudo apt-get ...", // [6]
          "raw_output": "Hit:1 http://archive.ubuntu.com/ubuntu focal ...", // [7]
          "packages": [ // [8]
           {
            "package": "nova-common", // [9]
            "from_version": "2:21.2.4-0ubuntu2.0", // [10]
            "to_version": "2:21.2.4-0ubuntu2.1" // [11]
           },
           {
            "package": "python3-nova",  // [9]
            "from_version": "2:21.2.4-0ubuntu2.0", // [10]
            "to_version": "2:21.2.4-0ubuntu2.1" // [11]
           }
          ],
          "success": true // [12]
         }
        ],
        "application": "nova-cloud-controller" // [13]
       }
      ]
     }
    ]
   }
  },
  "error": null
 }
]

```

* **[1]** copy of input
* **[2]** empty result if application is not matched
* **[3]** results if application is matched
* **[4]** list of units matched
* **[5]** unit name
* **[6]** command executed on unit
* **[7]** raw output of executed command
* **[8]** packages updated on unit
* **[9]** updated package name
* **[10]** updated package old version
* **[11]** updated package current version
* **[12]** update result
* **[13]** name of the application matched
