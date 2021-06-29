import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401


RESOLUTION = 'Free up Disk Space with Data Archiving: https://docs.paloaltonetworks.com/cortex/cortex-xsoar/6-0/' \
             'cortex-xsoar-admin/manage-data/free-up-disc-space-with-data-archiving'


def analyze_data(res):
    add_actions = []
    disk_usage = res[-1]['data'][0]
    thresholds = {
        90: 'High',
        80: 'Medium',
        70: 'Low',
    }

    for threshold, severity in thresholds.items():
        if disk_usage > threshold:
            add_actions.append({
                'category': 'Disk usage analysis',
                'severity': severity,
                'description': f'Disk usage has reached {threshold}%',
                'resolution': RESOLUTION,
            })
            break

    if (disk_usage - res[0]['data'][0]) > 1:
        add_actions.append({
            'category': 'Disk usage analysis',
            'severity': 'High',
            'description': "Disk usage was increased significantly in the last 24 hours",
            'resolution': RESOLUTION,
        })

    return add_actions


def main(args):
    incident = demisto.incident()
    is_widget = argToBoolean(args.get('isWidget', True))
    widget_type = "number" if is_widget else "line"

    partition = "/"
    if incident['CustomFields']["serverconfiguration"]:
        for entry in incident['CustomFields']["serverconfiguration"]:
            if entry.get('key', "") == 'disk.partitions.to.monitor':
                partition = entry['value']

    res = demisto.executeCommand(
        "demisto-api-post",
        {
            "uri": "/statistics/widgets/query",
            "body": {
                "size": 1440,
                "dataType": "system",
                "params": {
                    "timeFrame": "minutes"
                },
                "query": f"disk.usedPercent.{partition}",
                "dateRange": {
                    "period": {
                        "byFrom": "hours",
                        "fromValue": 24,
                    }
                },
                "widgetType": widget_type,
            }
        })
    if is_error(res):
        return_results(res)
        return_error('Failed to execute demisto-api-post. See additional error details in the above entries.')

    stats = res[0]["Contents"]["response"]
    data = {
        "Type": 17,
        "ContentsFormat": widget_type,
        "Contents": {
            "stats": stats,
            "params": {
                "currencySign": "%",
                "signAlignment": "right",
                "colors": {
                    "isEnabled": True,
                    "items": {
                        "#00CD33": {"value": -1},
                        "#FAC100": {"value": 60},
                        "#FF1B15": {"value": 80},
                    },
                    "type": "above",
                }
            }
        }
    }

    if is_widget:
        return data
    else:
        add_actions = analyze_data(res)
        return CommandResults(
            readable_output="analyzeCPUUsage Done",
            outputs_prefix="actionableitems",
            outputs=add_actions)


if __name__ in ('__main__', '__builtin__', 'builtins'):  # pragma: no cover
    return_results(main(demisto.args()))
