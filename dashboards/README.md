# AI DIAL Realtime Analytics Grafana Dashboards

This directory contains the two groups of Grafana dashboards for the AI DIAL Realtime Analytics project.

The [Customized](customized/) Grafana dashboards contain widgets that display aggregated data unavailable with the base installation. The data displayed by custom widgets is collected by additional DIAL components and configured exclusively for the specific needs of a particular client. In the absence of additional data, custom widgets will either display distorted metrics or remain empty.

In the case of a base DIAL installation, [Public](public/) Grafana dashboards should be used, which aggregate and display DIAL's basic metrics.

1. [Public](public/) Grafana dashboards for the AI DIAL Realtime Analytics project appplied for the general cases.
1. [Customized](customized/) Grafana dashboards for the AI DIAL Realtime Analytics project with the specisific data and widgets.