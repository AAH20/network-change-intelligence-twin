from __future__ import annotations
from typing import Any

def metric(name,category,value,unit,target,direction,evidence):
    passed=value>=target if direction=="higher" else value<=target
    return {"name":name,"category":category,"value":round(value,4),"unit":unit,"target":target,"direction":direction,"passed":passed,"evidence":evidence}

def scorecard(report: dict[str,Any], observations: dict[str,Any]) -> dict[str,Any]:
    candidate=report["candidate"]; paths=[x["path"] for x in candidate if x["path"]]
    m=[
      metric("revenue at risk","business",report["economics"]["revenue_at_risk_usd"],"USD",0,"lower","modeled synthetic economics"),
      metric("modeled avoided loss","business",report["economics"]["modeled_avoided_loss_usd"],"USD",10000,"higher","modeled synthetic economics"),
      metric("change validation ROI","business",report["economics"]["modeled_avoided_loss_usd"]/max(1,report["economics"]["validation_cost_usd"]),"ratio",3,"higher","modeled synthetic economics"),
      metric("intent compliance","change",sum(x["passed"] for x in candidate)/len(candidate)*100,"%",100,"higher","deterministic replay"),
      metric("failure scenario pass rate","change",sum(x["passed"] for x in report["failure_replay"])/len(report["failure_replay"])*100,"%",100,"higher","deterministic replay"),
      metric("predeployment detection","change",100 if report["decision"]["status"]=="hold" else 0,"%",100,"higher","deterministic replay"),
      metric("change success rate","change",observations["change_success_pct"],"%",98,"higher","synthetic observation"),
      metric("rollback success","change",observations["rollback_success_pct"],"%",100,"higher","synthetic observation"),
      metric("latency p95","network",max(x["latency_ms"] for x in paths),"ms",50,"lower","deterministic replay"),
      metric("minimum path bandwidth","network",min(x["bandwidth_mbps"] for x in paths),"Mbps",1000,"higher","deterministic replay"),
      metric("packet loss","network",observations["packet_loss_pct"],"%",.1,"lower","synthetic observation"),
      metric("jitter p95","network",observations["jitter_p95_ms"],"ms",10,"lower","synthetic observation"),
      metric("route convergence","network",observations["route_convergence_seconds"],"seconds",30,"lower","synthetic observation"),
      metric("encrypted path coverage","security",sum(x["encrypted"] for x in paths)/len(paths)*100,"%",100,"higher","deterministic replay"),
      metric("segmentation policy coverage","security",observations["segmentation_policy_pct"],"%",100,"higher","synthetic observation"),
      metric("unauthorized paths","security",observations["unauthorized_paths"],"count",0,"lower","synthetic observation"),
      metric("configuration compliance","compliance",observations["configuration_compliance_pct"],"%",99,"higher","synthetic observation"),
      metric("evidence completeness","compliance",observations["evidence_completeness_pct"],"%",100,"higher","synthetic observation"),
      metric("MTTD","operations",observations["mttd_minutes"],"minutes",5,"lower","synthetic observation"),
      metric("MTTR","operations",observations["mttr_minutes"],"minutes",30,"lower","synthetic observation"),
      metric("human minutes per change","operations",observations["human_minutes_per_change"],"minutes",30,"lower","synthetic observation"),
      metric("changes validated in twin","automation",observations["twin_validation_pct"],"%",100,"higher","synthetic observation"),
      metric("network automation coverage","automation",observations["network_automation_pct"],"%",95,"higher","synthetic observation"),
      metric("IaC coverage","automation",observations["iac_coverage_pct"],"%",100,"higher","synthetic observation"),
      metric("cloud egress per transaction","finops",observations["egress_cost_per_transaction_usd"],"USD",.01,"lower","synthetic observation"),
    ]
    hard={"no_autonomous_execution":not report["decision"]["automatic_execution"],"no_unauthorized_paths":next(x for x in m if x["name"]=="unauthorized paths")["passed"],"complete_evidence":next(x for x in m if x["name"]=="evidence completeness")["passed"]}
    return {"schema_version":"netchange/kpi/v1","summary":{"passed":sum(x["passed"] for x in m),"total":len(m),"attainment_pct":round(sum(x["passed"] for x in m)/len(m)*100,2)},"hard_gates":hard,"metrics":m,"claim_boundary":"Deterministic synthetic results and disclosed modeled observations are not production KPIs."}
