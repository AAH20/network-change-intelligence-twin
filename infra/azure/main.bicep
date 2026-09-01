param location string = resourceGroup().location
param suffix string = uniqueString(resourceGroup().id)

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'netchange-law-${suffix}'
  location: location
  properties: {retentionInDays: 30, sku: {name: 'PerGB2018'}}
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'netchange-ai-${suffix}'
  location: location
  kind: 'web'
  properties: {Application_Type: 'web', WorkspaceResourceId: logs.id}
}

output workspaceId string = logs.id
output claimBoundary string = 'Telemetry evidence plane only; no Azure network resource is changed.'
