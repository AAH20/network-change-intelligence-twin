from __future__ import annotations

import hashlib
import heapq
import json
from copy import deepcopy
from typing import Any


def validate(scenario: dict[str, Any]) -> None:
    required={"name","nodes","links","intents","changes","failure_scenarios","economics","kpi_observations"}
    missing=required-scenario.keys()
    if missing: raise ValueError("missing keys: "+", ".join(sorted(missing)))
    names={node["id"] for node in scenario["nodes"]}
    if len(names)!=len(scenario["nodes"]): raise ValueError("node ids must be unique")
    for link in scenario["links"]:
        if link["a"] not in names or link["b"] not in names: raise ValueError("link endpoint is unknown")
        if min(link["latency_ms"],link["bandwidth_mbps"],link["routing_weight"])<=0: raise ValueError("link metrics must be positive")


def apply_changes(links: list[dict[str,Any]], changes: list[dict[str,Any]]) -> list[dict[str,Any]]:
    proposed=deepcopy(links); by_id={link["id"]:link for link in proposed}
    for change in changes:
        if change["operation"]!="update_link" or change["link_id"] not in by_id: raise ValueError("unsupported or unknown change")
        allowed={"routing_weight","latency_ms","bandwidth_mbps","encrypted","cost_per_gb"}
        if not set(change["values"])<=allowed: raise ValueError("change modifies an unsupported field")
        by_id[change["link_id"]].update(change["values"])
    return proposed


def path(nodes: list[dict[str,Any]], links: list[dict[str,Any]], source: str, destination: str, failed_links: set[str]|None=None) -> dict[str,Any]|None:
    failed_links=failed_links or set(); graph={node["id"]:[] for node in nodes}
    for edge in links:
        if edge["id"] in failed_links: continue
        graph[edge["a"]].append((edge["b"],edge));graph[edge["b"]].append((edge["a"],edge))
    queue=[(0.0,source,[],[])];seen={}
    while queue:
        weight,current,node_path,edge_path=heapq.heappop(queue)
        if current in seen and seen[current]<=weight: continue
        seen[current]=weight
        if current==destination:
            latency=sum(x["latency_ms"] for x in edge_path);bandwidth=min((x["bandwidth_mbps"] for x in edge_path),default=0)
            return {"nodes":node_path+[current],"links":[x["id"] for x in edge_path],"routing_weight":weight,"latency_ms":latency,
                    "bandwidth_mbps":bandwidth,"encrypted":all(x["encrypted"] for x in edge_path),"cost_per_gb":round(sum(x["cost_per_gb"] for x in edge_path),4)}
        for neighbor,edge in graph[current]: heapq.heappush(queue,(weight+edge["routing_weight"],neighbor,node_path+[current],edge_path+[edge]))
    return None


def evaluate_intents(scenario: dict[str,Any], links: list[dict[str,Any]], failed_links: set[str]|None=None) -> list[dict[str,Any]]:
    results=[]
    for intent in scenario["intents"]:
        selected=path(scenario["nodes"],links,intent["source"],intent["destination"],failed_links);violations=[]
        if selected is None: violations.append("unreachable")
        else:
            if selected["latency_ms"]>intent["max_latency_ms"]: violations.append("latency")
            if selected["bandwidth_mbps"]<intent["min_bandwidth_mbps"]: violations.append("bandwidth")
            if intent["encryption_required"] and not selected["encrypted"]: violations.append("encryption")
            if selected["cost_per_gb"]>intent["max_cost_per_gb"]: violations.append("egress_cost")
        results.append({"intent":intent,"path":selected,"passed":not violations,"violations":violations})
    return results


def compile_change(scenario: dict[str,Any]) -> dict[str,Any]:
    validate(scenario);proposed=apply_changes(scenario["links"],scenario["changes"])
    baseline=evaluate_intents(scenario,scenario["links"]);candidate=evaluate_intents(scenario,proposed)
    failures=[]
    for failure in scenario["failure_scenarios"]:
        result=evaluate_intents(scenario,proposed,set(failure["failed_links"]))
        failures.append({"name":failure["name"],"intents":result,"passed":all(x["passed"] for x in result)})
    newly_failed=sum(1 for before,after in zip(baseline,candidate) if before["passed"] and not after["passed"])
    econ=scenario["economics"]
    revenue_per_minute=sum(x["transactions_per_minute"]*x["revenue_per_transaction_usd"] for x in scenario["intents"])
    exposure=revenue_per_minute*econ["assumed_incident_minutes"]*newly_failed
    avoided=exposure*econ["predeployment_detection_probability"]
    decision="hold" if newly_failed or not all(x["passed"] for x in failures) else "eligible-for-canary"
    report={"schema_version":"netchange/v1","scenario":scenario["name"],"baseline":baseline,"candidate":candidate,"failure_replay":failures,
            "economics":{"revenue_per_minute_usd":round(revenue_per_minute,2),"revenue_at_risk_usd":round(exposure,2),"modeled_avoided_loss_usd":round(avoided,2),"validation_cost_usd":econ["validation_cost_usd"],"modeled_net_value_usd":round(avoided-econ["validation_cost_usd"],2)},
            "decision":{"status":decision,"automatic_execution":False,"newly_failed_intents":newly_failed,"required_next_step":"revise change" if decision=="hold" else "bounded canary with independent approval"},
            "claim_boundary":"Deterministic graph replay with synthetic topology, traffic and economics; no vendor device, cloud account, Batfish, Containerlab or production network was operated."}
    canonical=json.dumps(report,sort_keys=True,separators=(",",":"));report["receipt_sha256"]=hashlib.sha256(canonical.encode()).hexdigest()
    return report
