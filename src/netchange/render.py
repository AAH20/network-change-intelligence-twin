import json
from pathlib import Path

def write(report,output:Path):
    output.mkdir(parents=True,exist_ok=True);(output/"change-decision.json").write_text(json.dumps(report,indent=2)+"\n")
    e=report["economics"];k=report["kpi_scorecard"]
    lines=["# Network change intelligence decision","",f"**Decision:** `{report['decision']['status']}`  ",f"**Receipt:** `{report['receipt_sha256']}`","",f"- Revenue at risk: **${e['revenue_at_risk_usd']:,.2f}**",f"- Modeled avoided loss: **${e['modeled_avoided_loss_usd']:,.2f}**",f"- Modeled net value: **${e['modeled_net_value_usd']:,.2f}**",f"- KPI attainment: **{k['summary']['passed']}/{k['summary']['total']} ({k['summary']['attainment_pct']}%)**","","## Candidate intent results",""]
    for item in report["candidate"]: lines.append(f"- **{item['intent']['name']}**: {'PASS' if item['passed'] else 'FAIL'} — {', '.join(item['violations']) or 'no violations'}")
    lines += ["","## Authority boundary","",report["claim_boundary"],"",k["claim_boundary"],""]
    (output/"change-decision.md").write_text("\n".join(lines))
