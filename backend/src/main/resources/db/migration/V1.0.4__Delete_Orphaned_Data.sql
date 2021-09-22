-- Deletes orphaned data (data without references for example WorkflowLinks without existing Workflows)
create or replace function delete_orphaned_data() returns integer
  language plpgsql
as $$
begin
  delete from workflowoperator where id not in (select workflowoperatorid from workflow_to_workflowoperator);
  delete from workflowlink_to_point where workflowlinkid not in (select workflowlinkid from workflow_to_workflowlink);
  delete from workflowlink where id not in (select workflowlinkid from workflow_to_workflowlink);
  delete from point where id not in (select pointid from workflowlink_to_point);
  delete from workflowio where id  not in (select workflowioid from workflowinput_to_workflowio union select workflowioid from workflowoutput_to_workflowio );
  return 0;
end;$$;

SELECT delete_orphaned_data();

