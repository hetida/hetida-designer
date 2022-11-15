# Reading Log Messages of Workflow and Component Executions

All log messages issued during the execution of a component or workflow contain the corresponding job id at the end of the message.

If the calculation of the output of a certain operator within a workflow is started and especially if an error occurs, the type (`tr type`), id (`tr id`), name (`tr name`), and tag (`tr tag`) of the transformation as well as the hierarchical nesting succession of the operator ids (`op id(s)`) and names (`op name(s)`) are additionally specified. The former helps to find and open e.g. a component via the sidebar in order to search for the error in the code, the latter helps to recognize at which point in the workflow and thus also with which input the error arose. 

```
2022-08-31 14:29:38,642 21583 INFO: Starting computation [in /home/mkuemmel/hetida-designer/runtime/hetdesrun/runtime/engine/plain/workflow.py:224, job id: 22fa6638-7df9-4f01-ab59-3d950f9942d6,
    tr type: COMPONENT, tr id: bfa27afc-dea8-b8aa-4b15-94402f0739b6, tr name: Pass Through (Series), tr tag: 1.0.0,
    op id(s): \56b74da9-2318-4707-b134-650048b0e61e\244973af-0daa-4d4e-9a6f-570642162b7f\4f1b4f7b-2f09-479f-961d-f79ae337b2ec\,
    op name(s): \Linear RUL from last positive Step\Data From Last Positive Step\Pass Through (Series) (2)\
]
```