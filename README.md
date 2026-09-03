# This repository is archived and no longer maintained. Delphix offers a fully supported Couchbase Select Connector — contact your Delphix Customer Success team for more information.

---

![](images/image1.png) 


## 
## What Does a Delphix Plugin Do?
Delphix is a data management platform that provides the ability to securely copy and share datasets. Using virtualization, you will ingest your data sources and create virtual data copies, which are full read-write capable database instances that use a small fraction of the resources a normal database copy would require. The Delphix engine has built-in support for interfacing with certain types of datasets, such as Oracle, SQL Server and ASE.

The Delphix virtualization SDK (https://github.com/delphix/virtualization-sdk) provides an interface for building custom data source integrations for the Delphix Dynamic Data Platform. The end users can design/implement a custom plugin which enable them to use custom data source like MongoDB, Cassandra, Couchbase or something else similar to as if they are using a built-in dataset type with Delphix Engine.

## About Couchbase Plugin:
Couchbase plugin is developed to virtualize couchbase data source leveraging the following built-in couchbase technologies:
  - Cross Data Center Replication (XDCR) allows data to be replicated across clusters that are potentially located in different data centers.
  - Cbbackupmgr allows data to be restored on staging host of Couchbase Server. 
  - Ingest Couchbase: Dsource can be created from a Couchbase cluster/single instance using (XDCR ingestion mechanism) or 
                    : Dsource can be created by restoring from a Couchbase backup peice using (CBBACKUPMGR ingestion mechanism) - Zero Touch Production.
  - Environment Discovery: Couchbase plugin can discover environments where Couchbase server is installed.
  - VDB Creation: Single node Couchbase VDB can be provisioned from the dsource snapshot.

### <a id="tested-versions"></a>User Documentation:
Documentation to install, build, upload and use the plugin is available at: https://delphix.github.io/couchbase-plugin.

### <a id="tested-versions"></a>Tested Versions:
- Delphix Engine: 5.3.x and 6.0.x
- Couchbase Version: 5.5 and 6.0
- Linux Version: RHEL 7.x

### <a id="support-features"></a>Supported Features:
- XDCR (Cross Data Center Replication).
- Couchbase Backup Manager.

### <a id="unsupported-features"></a>Unsupported Features:
- Backup documents as compressed.
- Incremental Backup Restore.

### <a id="known_issue"></a>Known Issues:
- Unable to build indexes during VDB provision.

### <a id="contribute"></a>How to Contribute:

Please refer [CONTRIBUTING.md](./CONTRIBUTING.md) to understand the pull requests process.

### <a id="statement-of-support"></a>Statement of Support:

This software is provided as-is, without warranty of any kind or commercial support through Delphix. See the associated license for additional details. Questions, issues, feature requests, and contributions should be directed to the community as outlined in the [Delphix Community Guidelines](https://delphix.github.io/community-guidelines.html).

### <a id="license"></a>License:

This is code is licensed under the Apache License 2.0. Full license is available [here](./LICENSE).

