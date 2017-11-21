# Translation Process Automation (TPA)

This repository hosts Translation Process Automation scripts which automate uploading translatable resource files and translated files between development repositories and localization platform.

## NOTE FOR TPA2 BRANCH

*NOTE:*
*Code in this branch is under development.*

This is successor of current TPA with major architecture changes as described below.

* Providers
    * TPA consists of providers.
    * A provider is responsible for specific service.
    * A provider provides service via REST API.
    * Providers can run on a single machine or different machines.

* Jobs
    * Flexible job configuration.
    * A job can consit of tasks.

* Tasks
    * Defines single unit of work.
    * Can be part of any jobs (re-usable).

* Logs
    * Utilize kafka to produce analytical reports.
 
