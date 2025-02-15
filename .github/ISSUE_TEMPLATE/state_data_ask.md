---
name: State Data Ask
about: Request to investigate or ingest state data about a certain topic.
title: '[US_XX] Title'
labels: 'External State Data Ask, Internal State Data Ask'
assignees: ''
---
> BEFORE YOU BEGIN!! PLEASE CHECK OFF AND COMPLETE THE FOLLOWING.
- [ ] I have added the `State Data Asks` project to the `Projects` section on the right hand panel.
- [ ] I have added the corresponding `REGION: US_XX` label associated with my request.
- [ ] `Internal State Data Ask` and `External State Data Ask` labels are both added by default. I have removed the one that doesn't apply.

_For questions on how to use the State Data Ask versus other data requests (Schema Change Request, DSCI Infra Request), please refer to [Data Request Instructions](https://docs.google.com/document/d/1WhBI9Sb5P9dFu8iTpqbca-hjJP31kM-XAQXwc3lQeDU/edit#)._

### Request Information				
#### Summary of data ask:
Summary of request. Please link any relevant docs, if applicable.

#### Specific tool/task this information is needed for:
What will this information be used for?

#### Deadline or Preferred Timeline (if applicable):
Deadline of the request. Ex: XX-YY-20ZZ, Within X week(s)/month(s), By End of 20XXQ1. If there isn't one, please state so.

#### Type of Data Request:
- [ ] One off request required for a specific task
- [ ] Recurring data that is needed for tools/products
- [ ] Other

*If other, please specify below:*

### Purpose & Needs
Please locate the state's [Ingest Catalog](https://app.gitbook.com/@recidiviz/s/recidiviz/) to see what state data is currently available and/or ingested.
- The _Schema Mappings_ tab indicates which state data has been ingested by Recidiviz.
- The _Raw Data Description_ tab lists all tables the state has provided, as well as descriptions for each.
    - In the `Table of Contents`, the `Referencing Views` column indicates that the table is ingested.

#### Based on the information you've seen above, do new files need to be requested and uploaded to GCS?
- [ ] Yes, the data I'm looking for seems to not be currently included in raw data provided by the state.
- [ ] No, new files don't seem to need to be requested.
- [ ] Maybe, there needs to be an investigation.

#### If new files don't need to be requested, which table(s) seem to contain the information you're looking for?

#### Additional context
Any other context needed to understand the data ask?

### STOP HERE! FOR ENG TO FILL OUT.
#### Data Needs to be Propagated to:
- [ ]  GCS bucket (raw file)
- [ ] BigQuery (raw file available and queryable on BQ)
- [ ] Postgres (data is ingested and mapped to schema, but not processed by calc pipeline)
- [ ] Dataflow metrics (data is ingested and processed by calc pipeline)
- [ ] Sessions (data is ingested, processed, and pulled by sessions views built by DADS)
- [ ] Other

*If other, then state the where it is needed below:*

#### Does the data need to be mapped to our [internal entity schema](https://app.gitbook.com/o/-MS0FZPVqDyJ1aem018G/s/-MRvK9sMirb5JcYHAkjo-887967055/schema-catalog/entities) and ingested? If so, then which entities will need to be hydrated?
List entities that will  need to be hydrated, if applicable.

#### Will there need to be calculation changes for Dataflow metrics (ex: new enums, custom logic)?
If there is custom/state-specific logic that will be required, mention so here.

#### Will an ingest rerun be required?
- [ ] No rerun will be required.
- [ ] A partial rerun will be required.
- [ ] A full rerun will be required.


#### Please provide any extra context if necessary:
